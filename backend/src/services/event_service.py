"""View and response recording for the recipient-facing preview.

Duplicate protection is layered: a read finds the common case cheaply, and the
partial unique index catches the concurrent case the read cannot. Either way a
duplicate returns 200 with the original event and ``deduplicated: true`` - a
double-click is not a client error and the preview must not show a failure
state for one.
"""

from __future__ import annotations

import hashlib

from sqlalchemy.exc import IntegrityError

from src.app.errors import ApiError
from src.models import Campaign, CampaignEvent
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.enums import CampaignStatus, EventType, FollowUpType
from src.schemas.event import EventRead, ResponseResult
from src.services.personalisation import PersonalisationContext, resolve
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import derive_effective_status, is_viewable_by_recipient
from src.services.validators_utm import append_utm_params


class EventService:
    def __init__(
        self,
        campaigns: CampaignRepository,
        events: EventRepository,
        *,
        ip_hash_salt: str = "",
    ) -> None:
        self._campaigns = campaigns
        self._events = events
        self._salt = ip_hash_salt

    async def record_view(
        self,
        campaign_id: str,
        session_id: str,
        *,
        recipient_id: str | None = None,
        user_agent: str | None = None,
        client_ip: str | None = None,
    ) -> EventRead:
        campaign = await self._require_live(campaign_id)

        existing = await self._events.find_by_session(campaign.id, session_id, EventType.VIEW)
        if existing is not None:
            return self._to_read(existing, deduplicated=True)

        event = CampaignEvent(
            campaign_id=campaign.id,
            experience_id=campaign.experience.id if campaign.experience else None,
            recipient_id=recipient_id,
            session_id=session_id,
            type=EventType.VIEW.value,
            user_agent=(user_agent or "")[:255] or None,
            ip_hash=self._hash_ip(client_ip),
        )

        return await self._insert(event, campaign.id, session_id, EventType.VIEW)

    async def record_response(
        self,
        campaign_id: str,
        session_id: str,
        option_id: str,
        *,
        recipient_id: str | None = None,
        user_agent: str | None = None,
        client_ip: str | None = None,
    ) -> ResponseResult:
        campaign = await self._require_live(campaign_id)
        option = self._require_option(campaign, option_id)

        existing = await self._events.find_by_session(campaign.id, session_id, EventType.RESPONSE)
        if existing is not None:
            # Return the follow-up for the option originally chosen, not the
            # one just clicked, so a double-click cannot switch the outcome.
            original = self._require_option(campaign, str(existing.option_id))
            return self._build_result(
                campaign, original, self._to_read(existing, deduplicated=True)
            )

        event = CampaignEvent(
            campaign_id=campaign.id,
            experience_id=campaign.experience.id if campaign.experience else None,
            recipient_id=recipient_id,
            option_id=option.id,
            session_id=session_id,
            type=EventType.RESPONSE.value,
            user_agent=(user_agent or "")[:255] or None,
            ip_hash=self._hash_ip(client_ip),
        )

        recorded = await self._insert(event, campaign.id, session_id, EventType.RESPONSE)
        return self._build_result(campaign, option, recorded)

    # --- helpers -----------------------------------------------------------

    async def _insert(
        self,
        event: CampaignEvent,
        campaign_id: str,
        session_id: str,
        event_type: EventType,
    ) -> EventRead:
        self._events.add(event)
        try:
            await self._events.commit()
        except IntegrityError:
            # Lost the race against a concurrent identical request. The other
            # one won; return its event rather than failing this caller.
            await self._events.rollback()
            existing = await self._events.find_by_session(campaign_id, session_id, event_type)
            if existing is None:
                raise
            return self._to_read(existing, deduplicated=True)

        return self._to_read(event, deduplicated=False)

    async def _require_live(self, campaign_id: str) -> Campaign:
        campaign = await self._campaigns.get_public(campaign_id)
        if campaign is None:
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")

        effective = derive_effective_status(
            status=CampaignStatus(campaign.status),
            start_at=campaign.start_at,
            end_at=campaign.end_at,
            is_publishable=not collect_publish_blockers(campaign),
        )
        if not is_viewable_by_recipient(effective):
            raise ApiError(
                403,
                "CAMPAIGN_NOT_LIVE",
                "This campaign is not currently available.",
            )

        return campaign

    @staticmethod
    def _require_option(campaign: Campaign, option_id: str):
        experience = campaign.experience
        options = experience.options if experience else []
        for option in options:
            if option.id == option_id:
                return option

        raise ApiError(
            422,
            "EVENT_INVALID_OPTION",
            "That response option does not belong to this campaign.",
        )

    def _build_result(self, campaign: Campaign, option, event: EventRead) -> ResponseResult:
        context = PersonalisationContext(
            customer_name=(campaign.recipients[0].customer_name if campaign.recipients else None),
            campaign_name=campaign.name,
            option_label=option.label,
        )

        follow_up_url = option.follow_up_url
        if follow_up_url:
            follow_up_url = append_utm_params(
                follow_up_url,
                {
                    "utm_source": campaign.utm_source,
                    "utm_medium": campaign.utm_medium,
                    "utm_campaign": campaign.utm_campaign,
                    "utm_content": campaign.utm_content or option.key,
                },
            )

        message = (
            resolve(option.follow_up_message, context).text
            if option.follow_up_type == FollowUpType.MESSAGE.value
            else None
        )

        return ResponseResult(
            event=event,
            follow_up_type=option.follow_up_type,
            follow_up_message=message,
            follow_up_url=follow_up_url,
        )

    def _hash_ip(self, client_ip: str | None) -> str | None:
        """SHA-256 of IP + server salt. The raw address is never stored."""
        if not client_ip or not self._salt:
            return None
        return hashlib.sha256(f"{self._salt}:{client_ip}".encode()).hexdigest()

    @staticmethod
    def _to_read(event: CampaignEvent, *, deduplicated: bool) -> EventRead:
        return EventRead(
            id=event.id,
            type=EventType(event.type),
            session_id=event.session_id,
            option_id=event.option_id,
            occurred_at=event.occurred_at,
            deduplicated=deduplicated,
        )

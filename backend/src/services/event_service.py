"""View and response recording for the viewer-facing preview.

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
from src.models.audience import AudienceMember
from src.repositories.audience_repository import AudienceRepository
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
        audiences: AudienceRepository,
        *,
        ip_hash_salt: str = "",
    ) -> None:
        self._campaigns = campaigns
        self._events = events
        self._audiences = audiences
        self._salt = ip_hash_salt

    async def record_view(
        self,
        campaign_id: str,
        session_id: str,
        *,
        ad_id: str | None = None,
        member_id: str | None = None,
        user_agent: str | None = None,
        client_ip: str | None = None,
    ) -> EventRead:
        campaign = await self._require_live(campaign_id)
        ad = self._resolve_ad(campaign, ad_id)

        existing = await self._events.find_by_session(campaign.id, session_id, EventType.VIEW)
        if existing is not None:
            return self._to_read(existing, deduplicated=True)

        event = CampaignEvent(
            campaign_id=campaign.id,
            ad_id=ad.id if ad else None,
            member_id=member_id,
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
        ad_id: str | None = None,
        member_id: str | None = None,
        user_agent: str | None = None,
        client_ip: str | None = None,
    ) -> ResponseResult:
        campaign = await self._require_live(campaign_id)
        ad, option = self._require_option(campaign, option_id)

        existing = await self._events.find_by_session(campaign.id, session_id, EventType.RESPONSE)
        if existing is not None:
            # Return the follow-up for the option originally chosen, not the
            # one just clicked, so a double-click cannot switch the outcome.
            # Personalised for whoever the original event named, for the same
            # reason: the second click must render exactly like the first.
            _, original = self._require_option(campaign, str(existing.option_id))
            return await self._build_result(
                campaign,
                original,
                self._to_read(existing, deduplicated=True),
                member_id=existing.member_id,
            )

        event = CampaignEvent(
            campaign_id=campaign.id,
            ad_id=ad.id,
            member_id=member_id,
            option_id=option.id,
            session_id=session_id,
            type=EventType.RESPONSE.value,
            user_agent=(user_agent or "")[:255] or None,
            ip_hash=self._hash_ip(client_ip),
        )

        recorded = await self._insert(event, campaign.id, session_id, EventType.RESPONSE)
        return await self._build_result(campaign, option, recorded, member_id=member_id)

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
    def _resolve_ad(campaign: Campaign, ad_id: str | None):
        """Which creative this event happened on.

        Without an id the campaign's primary ad is assumed, which is what the
        single-ad flow has always done implicitly.
        """
        if ad_id is None:
            return campaign.primary_ad

        for ad in campaign.ads:
            if ad.id == ad_id:
                return ad

        raise ApiError(404, "AD_NOT_FOUND", "No ad with that id on this campaign.")

    async def _member(self, campaign: Campaign, member_id: str | None) -> AudienceMember | None:
        """The person a follow-up is addressed to.

        Resolved exactly as ``PreviewService._select_member`` resolves it,
        including the fall back to the audience's first member when the link
        names nobody. The two must agree: they are the two halves of one
        interaction, and a video that opens "Hi Rahul" followed by "Great,
        there - an advisor will call" is a bug the recipient sees.

        That fallback is also what makes the brief's single-customer case work
        - an audience of one, opened from a link that carries no member id.
        """
        if campaign.audience_id is None:
            return None

        if member_id is None:
            return await self._audiences.first_member(campaign.audience_id)

        return await self._audiences.get_member(campaign.audience_id, member_id)

    @staticmethod
    def _require_option(campaign: Campaign, option_id: str):
        """Find an option anywhere in the campaign, and the ad that owns it.

        Searching every ad rather than one is what makes ``ad_id`` optional on
        a response: the option id already identifies its creative unambiguously.
        """
        for ad in campaign.ads:
            for option in ad.options:
                if option.id == option_id:
                    return ad, option

        raise ApiError(
            422,
            "EVENT_INVALID_OPTION",
            "That response option does not belong to this campaign.",
        )

    async def _build_result(
        self, campaign: Campaign, option, event: EventRead, *, member_id: str | None
    ) -> ResponseResult:
        # Resolved against whoever the link named, and against the same
        # fallback the preview used when it named nobody.
        member = await self._member(campaign, member_id)

        context = PersonalisationContext(
            customer_name=member.full_name if member else None,
            campaign_name=campaign.name,
            option_label=option.label,
            city=member.city if member else None,
            country=member.country if member else None,
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

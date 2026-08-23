"""Campaign business logic.

Owns creation, editing, the publish contract and lifecycle transitions. Knows
nothing about HTTP: it raises ApiError, which the error handler turns into a
response.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from src.app.errors import ApiError
from src.models import Campaign, CampaignOption, Experience, Recipient
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.campaign import (
    CampaignCreate,
    CampaignListItem,
    CampaignPage,
    CampaignRead,
    CampaignUpdate,
)
from src.schemas.enums import (
    DEFAULT_DISCLAIMERS,
    AudienceType,
    CampaignStatus,
    SpecialCategory,
)
from src.schemas.experience import ExperienceInput
from src.schemas.recipient import RecipientInput
from src.services import mappers
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import (
    UNPUBLISH_TARGET,
    is_transition_allowed,
    resolve_publish_target,
)
from src.services.validators_utm import default_utm_campaign


class CampaignService:
    def __init__(self, campaigns: CampaignRepository, events: EventRepository) -> None:
        self._campaigns = campaigns
        self._events = events

    # --- reads -------------------------------------------------------------

    async def get(self, campaign_id: str, owner_user_id: str) -> CampaignRead:
        campaign = await self._require(campaign_id, owner_user_id)
        counts = await self._events.counts_by_type(campaign.id)
        _, last = await self._events.activity_window(campaign.id)

        return mappers.campaign_to_read(campaign, metrics=mappers.build_metrics(counts, last))

    async def list_campaigns(
        self,
        owner_user_id: str,
        *,
        status: CampaignStatus | None = None,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> CampaignPage:
        campaigns, total = await self._campaigns.list_campaigns(
            owner_user_id,
            status=status,
            search=search,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )

        # Two aggregate queries for the whole page, not two per row.
        ids = [c.id for c in campaigns]
        counts = await self._events.counts_for_campaigns(ids)
        last_seen = await self._events.last_activity_for_campaigns(ids)

        items: list[CampaignListItem] = [
            mappers.campaign_to_list_item(
                campaign,
                metrics=mappers.build_metrics(
                    counts.get(campaign.id, {}), last_seen.get(campaign.id)
                ),
            )
            for campaign in campaigns
        ]

        return CampaignPage(items=items, total=total, limit=limit, offset=offset)

    # --- writes ------------------------------------------------------------

    async def create(self, payload: CampaignCreate, owner_user_id: str) -> CampaignRead:
        await self._guard_name(owner_user_id, payload.name)

        campaign = Campaign(owner_user_id=owner_user_id, name=payload.name)
        self._apply_scalar_fields(campaign, payload)

        experience = Experience(campaign=campaign)
        self._apply_experience(experience, payload.experience)
        campaign.experiences.append(experience)

        self._replace_recipients(campaign, payload.recipients)
        self._enforce_audience_rule(campaign)

        self._campaigns.add(campaign)
        await self._commit(owner_user_id, campaign.name)

        # Re-read rather than mapping the in-memory instance: a collection that
        # was cleared but never populated is not marked loaded, and touching it
        # after commit would emit a lazy SELECT outside the async context.
        return await self.get(campaign.id, owner_user_id)

    async def update(
        self, campaign_id: str, payload: CampaignUpdate, owner_user_id: str
    ) -> CampaignRead:
        campaign = await self._require(campaign_id, owner_user_id)
        supplied = payload.model_dump(exclude_unset=True)

        if campaign.status == CampaignStatus.ARCHIVED.value:
            raise ApiError(
                409,
                "CAMPAIGN_INVALID_TRANSITION",
                "An archived campaign cannot be edited. Duplicate it to run it again.",
            )

        if "name" in supplied and payload.name and payload.name != campaign.name:
            await self._guard_name(owner_user_id, payload.name, exclude_id=campaign.id)
            campaign.name = payload.name

        # The objective decides what historical metrics mean, so it freezes
        # once the campaign has been published.
        if "objective" in supplied and payload.objective:
            if campaign.published_at and payload.objective.value != campaign.objective:
                raise ApiError(
                    409,
                    "CAMPAIGN_LOCKED",
                    "The objective cannot change after a campaign has been published.",
                )
            campaign.objective = payload.objective.value

        if "description" in supplied:
            campaign.description = payload.description
        if "audience_type" in supplied and payload.audience_type:
            campaign.audience_type = payload.audience_type.value

        if payload.schedule is not None:
            campaign.start_at = payload.schedule.start_at
            campaign.end_at = payload.schedule.end_at
            campaign.timezone = payload.schedule.timezone
        if payload.budget is not None:
            campaign.budget_type = payload.budget.budget_type.value
            campaign.budget_amount_minor = payload.budget.budget_amount_minor
            campaign.currency = payload.budget.currency
            campaign.spend_cap_minor = payload.budget.spend_cap_minor
        if payload.delivery is not None:
            campaign.pacing = payload.delivery.pacing.value
            campaign.send_cap_total = payload.delivery.send_cap_total
            campaign.send_cap_per_day = payload.delivery.send_cap_per_day
            campaign.frequency_cap_per_recipient = payload.delivery.frequency_cap_per_recipient
        if payload.compliance is not None:
            campaign.special_category = payload.compliance.special_category.value
            campaign.disclaimer_text = payload.compliance.disclaimer_text
        if payload.tracking is not None:
            campaign.utm_source = payload.tracking.utm_source
            campaign.utm_medium = payload.tracking.utm_medium
            campaign.utm_campaign = payload.tracking.utm_campaign
            campaign.utm_content = payload.tracking.utm_content
            campaign.external_ref = payload.tracking.external_ref

        if payload.experience is not None:
            experience = campaign.experience
            if experience is None:
                experience = Experience(campaign=campaign)
                campaign.experiences.append(experience)
            self._apply_experience(experience, payload.experience)

        if payload.recipients is not None:
            self._replace_recipients(campaign, payload.recipients)

        self._enforce_audience_rule(campaign)
        campaign.updated_at = datetime.now(UTC)

        await self._commit(owner_user_id, campaign.name)

        return await self.get(campaign.id, owner_user_id)

    async def change_status(
        self, campaign_id: str, target: CampaignStatus, owner_user_id: str
    ) -> CampaignRead:
        campaign = await self._require(campaign_id, owner_user_id)
        current = CampaignStatus(campaign.status)

        if not is_transition_allowed(current, target):
            raise ApiError(
                409,
                "CAMPAIGN_INVALID_TRANSITION",
                f"A campaign cannot move from {current.value} to {target.value}.",
            )

        if target in {CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED}:
            blockers = collect_publish_blockers(campaign)
            if blockers:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "The campaign cannot be published.",
                    details=[b.as_detail() for b in blockers],
                )

            resolved = resolve_publish_target(campaign.start_at)
            campaign.status = resolved.value
            if campaign.published_at is None:
                campaign.published_at = datetime.now(UTC)
            if not campaign.utm_campaign:
                campaign.utm_campaign = default_utm_campaign(campaign.name)

        elif target is UNPUBLISH_TARGET and current is not CampaignStatus.DRAFT:
            # Once a real customer has seen it, content is frozen against
            # silent rewriting.
            counts = await self._events.counts_by_type(campaign.id)
            if sum(counts.values()) > 0:
                raise ApiError(
                    409,
                    "CAMPAIGN_LOCKED",
                    "This campaign has recorded activity and can no longer be "
                    "returned to draft. Duplicate it instead.",
                )
            campaign.status = target.value

        else:
            campaign.status = target.value
            if target is CampaignStatus.ARCHIVED:
                campaign.archived_at = datetime.now(UTC)

        campaign.updated_at = datetime.now(UTC)
        await self._commit(owner_user_id, campaign.name)

        return await self.get(campaign.id, owner_user_id)

    async def delete(self, campaign_id: str, owner_user_id: str) -> None:
        campaign = await self._require(campaign_id, owner_user_id)
        await self._campaigns.delete(campaign)
        await self._campaigns.commit()

    # --- helpers -----------------------------------------------------------

    async def _require(self, campaign_id: str, owner_user_id: str) -> Campaign:
        campaign = await self._campaigns.get(campaign_id, owner_user_id)
        if campaign is None:
            # A campaign owned by someone else is reported as not found rather
            # than forbidden, so ids cannot be probed for existence.
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")
        return campaign

    async def _guard_name(
        self, owner_user_id: str, name: str, *, exclude_id: str | None = None
    ) -> None:
        if await self._campaigns.name_exists(owner_user_id, name, exclude_id=exclude_id):
            raise ApiError(
                409,
                "CAMPAIGN_NAME_TAKEN",
                "You already have a campaign with that name.",
                details=[
                    {
                        "field": "name",
                        "code": "DUPLICATE",
                        "message": "Choose a different campaign name.",
                    }
                ],
            )

    async def _commit(self, owner_user_id: str, name: str) -> None:
        """Commit, translating the unique index into a field-level error.

        The pre-check in _guard_name is advisory; this catches the race where
        two concurrent requests both pass it.
        """
        try:
            await self._campaigns.commit()
        except IntegrityError as exc:
            await self._campaigns.rollback()
            if "uniq_campaign_owner_name" in str(exc.orig):
                raise ApiError(
                    409,
                    "CAMPAIGN_NAME_TAKEN",
                    "You already have a campaign with that name.",
                ) from exc
            raise ApiError(
                409, "CONSTRAINT_VIOLATION", "The change conflicts with existing data."
            ) from exc

    def _apply_scalar_fields(self, campaign: Campaign, payload: CampaignCreate) -> None:
        campaign.description = payload.description
        campaign.objective = payload.objective.value
        campaign.audience_type = payload.audience_type.value

        campaign.start_at = payload.schedule.start_at
        campaign.end_at = payload.schedule.end_at
        campaign.timezone = payload.schedule.timezone

        campaign.budget_type = payload.budget.budget_type.value
        campaign.budget_amount_minor = payload.budget.budget_amount_minor
        campaign.currency = payload.budget.currency
        campaign.spend_cap_minor = payload.budget.spend_cap_minor

        campaign.pacing = payload.delivery.pacing.value
        campaign.send_cap_total = payload.delivery.send_cap_total
        campaign.send_cap_per_day = payload.delivery.send_cap_per_day
        campaign.frequency_cap_per_recipient = payload.delivery.frequency_cap_per_recipient

        campaign.special_category = payload.compliance.special_category.value
        campaign.disclaimer_text = payload.compliance.disclaimer_text or self._default_disclaimer(
            payload.compliance.special_category
        )

        campaign.utm_source = payload.tracking.utm_source
        campaign.utm_medium = payload.tracking.utm_medium
        campaign.utm_campaign = payload.tracking.utm_campaign or default_utm_campaign(payload.name)
        campaign.utm_content = payload.tracking.utm_content
        campaign.external_ref = payload.tracking.external_ref

    @staticmethod
    def _default_disclaimer(category: SpecialCategory) -> str | None:
        return DEFAULT_DISCLAIMERS.get(category)

    @staticmethod
    def _apply_experience(experience: Experience, payload: ExperienceInput) -> None:
        experience.video_url = payload.video_url
        experience.poster_url = payload.poster_url
        experience.captions_url = payload.captions_url
        experience.video_duration_seconds = payload.video_duration_seconds
        experience.headline = payload.headline
        experience.personalised_message = payload.personalised_message

        # Options are reconciled by position rather than cleared and re-added.
        # Delete-orphan plus a fresh insert makes SQLAlchemy emit the INSERT
        # before the DELETE in one flush, which trips uniq_option_position.
        # Updating in place also keeps each option's analytics key, so
        # rewording a label does not split its metric into two series.
        existing = {option.position: option for option in experience.options}
        incoming = {option.position: option for option in payload.options}

        for position, option_input in sorted(incoming.items()):
            option = existing.get(position)
            if option is None:
                option = CampaignOption(position=position, key=option_input.derive_key())
                experience.options.append(option)

            option.label = option_input.label or f"Option {position}"
            option.intent = option_input.intent.value
            option.follow_up_type = option_input.follow_up_type.value
            option.follow_up_message = option_input.follow_up_message
            option.follow_up_url = option_input.follow_up_url

        for position, option in existing.items():
            if position not in incoming:
                experience.options.remove(option)

    @staticmethod
    def _replace_recipients(campaign: Campaign, recipients: list[RecipientInput]) -> None:
        campaign.recipients.clear()
        for recipient in recipients:
            campaign.recipients.append(
                Recipient(
                    customer_name=recipient.customer_name,
                    email=str(recipient.email) if recipient.email else None,
                    phone=recipient.phone,
                    external_ref=recipient.external_ref,
                    attributes=recipient.attributes,
                )
            )

    @staticmethod
    def _enforce_audience_rule(campaign: Campaign) -> None:
        if campaign.audience_type == AudienceType.SINGLE.value and len(campaign.recipients) > 1:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "A single-recipient campaign cannot have more than one recipient.",
                details=[
                    {
                        "field": "recipients",
                        "code": "TOO_MANY",
                        "message": "Set audience_type to LIST to add more than one recipient.",
                    }
                ],
            )

"""Builds the recipient-facing preview payload.

The only response served without a Clerk session, so it is assembled from an
explicit allow-list rather than by trimming an internal model: nothing about
the owner, budget, delivery caps, other recipients or unclicked follow-ups
appears here.
"""

from __future__ import annotations

from src.app.errors import ApiError
from src.models import Campaign
from src.repositories.campaign_repository import CampaignRepository
from src.schemas.enums import CampaignStatus
from src.schemas.experience import ExperiencePublic
from src.schemas.option import OptionPublic
from src.schemas.preview import CampaignPreview, PreviewCompliance
from src.services.personalisation import (
    PersonalisationContext,
    resolve,
    unknown_variables,
)
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import derive_effective_status, is_viewable_by_recipient


class PreviewService:
    def __init__(self, campaigns: CampaignRepository) -> None:
        self._campaigns = campaigns

    async def get_public_preview(
        self, campaign_id: str, *, recipient_id: str | None = None
    ) -> CampaignPreview:
        """The live campaign as a recipient sees it."""
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
            raise ApiError(403, "CAMPAIGN_NOT_LIVE", "This campaign is not currently available.")

        return self._render(campaign, recipient_id=recipient_id)

    async def get_owner_preview(
        self, campaign_id: str, owner_user_id: str, *, recipient_id: str | None = None
    ) -> CampaignPreview:
        """The same render, for the builder's own preview.

        Scoped to the owner and allowed at any status, so a draft can be
        previewed before it is published.
        """
        campaign = await self._campaigns.get(campaign_id, owner_user_id)
        if campaign is None:
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")

        return self._render(campaign, recipient_id=recipient_id)

    def _render(self, campaign: Campaign, *, recipient_id: str | None) -> CampaignPreview:
        experience = campaign.experience
        if experience is None or not experience.video_url:
            raise ApiError(
                422,
                "CAMPAIGN_INCOMPLETE",
                "This campaign has no video configured yet.",
            )

        recipient = self._select_recipient(campaign, recipient_id)
        context = PersonalisationContext(
            customer_name=recipient.customer_name if recipient else None,
            campaign_name=campaign.name,
        )

        headline = resolve(experience.headline, context)
        message = resolve(experience.personalised_message, context)

        unresolved = sorted(
            set(headline.unresolved)
            | set(message.unresolved)
            | {
                name
                for option in experience.options
                for name in unknown_variables(option.follow_up_message)
            }
        )

        return CampaignPreview(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            customer_name=context.as_mapping()["customer_name"],
            recipient_id=recipient.id if recipient else None,
            experience=ExperiencePublic(
                id=experience.id,
                video_url=experience.video_url,
                poster_url=experience.poster_url,
                captions_url=experience.captions_url,
                headline=headline.text or None,
                personalised_message=message.text,
                options=[
                    OptionPublic(
                        id=option.id,
                        position=option.position,
                        key=option.key,
                        label=option.label,
                    )
                    for option in sorted(experience.options, key=lambda o: o.position)
                ],
            ),
            compliance=PreviewCompliance(
                special_category=campaign.special_category,
                disclaimer_text=campaign.disclaimer_text,
            ),
            unresolved_variables=unresolved,
        )

    @staticmethod
    def _select_recipient(campaign: Campaign, recipient_id: str | None):
        if not campaign.recipients:
            return None

        if recipient_id is None:
            return campaign.recipients[0]

        for recipient in campaign.recipients:
            if recipient.id == recipient_id:
                return recipient

        raise ApiError(404, "RECIPIENT_NOT_FOUND", "No recipient with that id on this campaign.")

"""Campaign aggregate root."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKey
from src.models.types import UTCDateTime
from src.schemas.enums import (
    AdStatus,
    BudgetType,
    CampaignObjective,
    CampaignStatus,
    PacingType,
    SpecialCategory,
)


class Campaign(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "campaigns"

    # Clerk user id (e.g. "user_2abc..."). Clerk owns the user record, so this
    # is a plain string with no foreign key and no local users table.
    owner_user_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    objective: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CampaignObjective.ENGAGEMENT.value
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CampaignStatus.DRAFT.value, index=True
    )

    # Schedule
    start_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    end_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")

    # Budget - integer minor units only, never a float.
    budget_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=BudgetType.NONE.value
    )
    budget_amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    spend_cap_minor: Mapped[int | None] = mapped_column(BigInteger)

    # Delivery
    pacing: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PacingType.STANDARD.value
    )
    send_cap_total: Mapped[int | None] = mapped_column(Integer)
    send_cap_per_day: Mapped[int | None] = mapped_column(Integer)
    frequency_cap_per_recipient: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Compliance
    special_category: Mapped[str] = mapped_column(
        String(48), nullable=False, default=SpecialCategory.NONE.value
    )
    disclaimer_text: Mapped[str | None] = mapped_column(String(500))

    # Tracking
    utm_source: Mapped[str | None] = mapped_column(String(80), default="trustvid")
    utm_medium: Mapped[str | None] = mapped_column(String(80), default="interactive-video")
    utm_campaign: Mapped[str | None] = mapped_column(String(80))
    utm_content: Mapped[str | None] = mapped_column(String(80))
    external_ref: Mapped[str | None] = mapped_column(String(120), index=True)

    # Audience - a reference to a reusable list, not a private copy of one.
    # SET NULL rather than CASCADE: deleting a list must never delete the
    # campaigns that once used it, or their analytics. The campaign simply
    # falls back to unpublishable until another audience is selected.
    audience_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("audiences.id", ondelete="SET NULL"), index=True
    )

    # Lifecycle
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    ads = relationship(
        "Ad",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Ad.created_at",
    )
    # Eager, and deliberately so: `member_count` is read on every campaign
    # read to decide whether the campaign can be published, and a lazy load
    # there would be an implicit query outside the async context.
    audience = relationship("Audience", back_populates="campaigns", lazy="selectin")
    events = relationship(
        "CampaignEvent",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="noload",  # never loaded implicitly; analytics aggregates in SQL
    )

    __table_args__ = (
        # Name uniqueness is enforced per owner at the database, so a race
        # between two concurrent creates cannot both win.
        Index(
            "uniq_campaign_owner_name",
            "owner_user_id",
            func.lower(name),
            unique=True,
        ),
        Index("idx_campaign_owner_status_created", "owner_user_id", "status", "created_at"),
        CheckConstraint(
            "budget_type = 'NONE' OR budget_amount_minor IS NOT NULL",
            name="ck_budget_amount_required",
        ),
        CheckConstraint(
            "spend_cap_minor IS NULL OR budget_amount_minor IS NULL "
            "OR spend_cap_minor >= budget_amount_minor",
            name="ck_spend_cap_gte_budget",
        ),
        CheckConstraint(
            "end_at IS NULL OR start_at IS NULL OR end_at > start_at",
            name="ck_end_after_start",
        ),
        CheckConstraint(
            "special_category = 'NONE' OR disclaimer_text IS NOT NULL",
            name="ck_disclaimer_required_for_category",
        ),
    )

    @property
    def primary_ad(self):
        """The ad a viewer sees when they open the campaign without naming one.

        The first ad that could actually be delivered - switched on, and
        complete - falling back to the first ad of any kind so that the
        builder's own preview still renders a half-built draft.
        """
        if not self.ads:
            return None

        for ad in self.ads:
            if ad.status == AdStatus.ACTIVE.value and ad.is_complete:
                return ad

        return self.ads[0]

    @property
    def live_ads(self) -> list:
        """Every ad that is switched on and complete, in creation order."""
        return [ad for ad in self.ads if ad.status == AdStatus.ACTIVE.value and ad.is_complete]

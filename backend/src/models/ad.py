"""Ad (the creative) and its response options.

An ad is what a recipient actually watches: a video, the copy around it, a
call to action, and the two response buttons. A campaign owns many of them.

The two-level split follows Meta's: the **campaign** carries the objective,
schedule, budget, audience and compliance - the things that are true of the
whole effort - and each **ad** carries one creative and its own status, so a
single creative can be paused without touching the rest of the campaign.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKey
from src.schemas.enums import AdStatus, CallToAction, FollowUpType, OptionIntent


class Ad(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "campaign_ads"

    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Internal label. Once a campaign holds several ads, "the experience" stops
    # being a way to refer to one of them.
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AdStatus.DRAFT.value, index=True
    )

    video_url: Mapped[str | None] = mapped_column(String(2048))
    poster_url: Mapped[str | None] = mapped_column(String(2048))
    captions_url: Mapped[str | None] = mapped_column(String(2048))
    video_duration_seconds: Mapped[int | None] = mapped_column(Integer)

    # Recipient-facing copy. `headline` is the title above the video and
    # `description` the supporting line beneath it - both are read by the
    # customer, unlike `campaigns.description`, which is an internal note.
    headline: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(500))
    personalised_message: Mapped[str | None] = mapped_column(Text)

    # Names the intent of the POSITIVE option and supplies its default label.
    cta: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CallToAction.LEARN_MORE.value
    )

    campaign = relationship("Campaign", back_populates="ads")
    options = relationship(
        "AdOption",
        back_populates="ad",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AdOption.position",
    )

    __table_args__ = (
        # Ad names are unique within their campaign, case-insensitively -
        # the same rule campaigns have within an owner, one level down.
        Index("uniq_ad_name_per_campaign", "campaign_id", func.lower(name), unique=True),
        Index("idx_ad_campaign_status", "campaign_id", "status"),
    )

    @property
    def is_complete(self) -> bool:
        """Whether this ad has everything a recipient needs to see it.

        Deliberately narrow: it answers "can this be shown", not "should it
        be". Whether it *is* being shown is
        ``status_service.derive_ad_effective_status``.
        """
        if not self.video_url or not self.personalised_message:
            return False
        if len(self.options) != 2:
            return False
        return all(option.is_complete for option in self.options)


class AdOption(UUIDPrimaryKey, TimestampMixin, Base):
    """A response button.

    Stored as rows rather than option_1_* / option_2_* columns, so a third
    option is data instead of a migration and analytics never needs a UNION.
    """

    __tablename__ = "ad_options"

    ad_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaign_ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Stable analytics key, slugged from the label at creation time. Rewording
    # a label must not split the metric into two series.
    key: Mapped[str] = mapped_column(String(60), nullable=False)

    label: Mapped[str] = mapped_column(String(40), nullable=False)
    intent: Mapped[str] = mapped_column(
        String(16), nullable=False, default=OptionIntent.NEUTRAL.value
    )
    follow_up_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=FollowUpType.MESSAGE.value
    )
    follow_up_message: Mapped[str | None] = mapped_column(Text)
    follow_up_url: Mapped[str | None] = mapped_column(String(2048))

    ad = relationship("Ad", back_populates="options")

    __table_args__ = (
        Index("uniq_option_position", "ad_id", "position", unique=True),
        Index("uniq_option_key", "ad_id", "key", unique=True),
        CheckConstraint("position IN (1, 2)", name="ck_option_position"),
        CheckConstraint(
            "(follow_up_type = 'MESSAGE' AND follow_up_message IS NOT NULL) "
            "OR (follow_up_type = 'URL' AND follow_up_url IS NOT NULL) "
            "OR (follow_up_message IS NULL AND follow_up_url IS NULL)",
            name="ck_follow_up_matches_type",
        ),
    )

    @property
    def is_complete(self) -> bool:
        """A label, and a follow-up matching the declared type."""
        if not self.label:
            return False
        if self.follow_up_type == FollowUpType.URL.value:
            return bool(self.follow_up_url)
        return bool(self.follow_up_message)

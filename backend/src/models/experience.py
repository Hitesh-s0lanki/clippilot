"""Experience (the creative) and its response options."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKey
from src.schemas.enums import FollowUpType, OptionIntent


class Experience(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "campaign_experiences"

    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    video_url: Mapped[str | None] = mapped_column(String(2048))
    poster_url: Mapped[str | None] = mapped_column(String(2048))
    captions_url: Mapped[str | None] = mapped_column(String(2048))
    video_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    headline: Mapped[str | None] = mapped_column(String(80))
    personalised_message: Mapped[str | None] = mapped_column(Text)

    campaign = relationship("Campaign", back_populates="experiences")
    options = relationship(
        "CampaignOption",
        back_populates="experience",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CampaignOption.position",
    )


class CampaignOption(UUIDPrimaryKey, TimestampMixin, Base):
    """A response button.

    Stored as rows rather than option_1_* / option_2_* columns, so a third
    option is data instead of a migration and analytics never needs a UNION.
    """

    __tablename__ = "campaign_options"

    experience_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaign_experiences.id", ondelete="CASCADE"),
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

    experience = relationship("Experience", back_populates="options")

    __table_args__ = (
        Index("uniq_option_position", "experience_id", "position", unique=True),
        Index("uniq_option_key", "experience_id", "key", unique=True),
        CheckConstraint("position IN (1, 2)", name="ck_option_position"),
        CheckConstraint(
            "(follow_up_type = 'MESSAGE' AND follow_up_message IS NOT NULL) "
            "OR (follow_up_type = 'URL' AND follow_up_url IS NOT NULL) "
            "OR (follow_up_message IS NULL AND follow_up_url IS NULL)",
            name="ck_follow_up_matches_type",
        ),
    )

"""View and response events.

Duplicate protection is enforced by partial unique indexes in the database
rather than an application-level check, so two concurrent requests cannot both
insert. Partial indexes work identically on SQLite and Postgres.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import UUIDPrimaryKey, utcnow
from src.models.types import UTCDateTime


class CampaignEvent(UUIDPrimaryKey, Base):
    __tablename__ = "campaign_events"

    # Denormalised so analytics never joins through ads to count a view, and
    # so the count survives the ad it happened on being deleted.
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Which creative was on screen. SET NULL rather than CASCADE: deleting one
    # ad must not erase the campaign's view history, and campaign_id is what
    # every rollup counts on. The per-ad breakdown simply loses that ad's row.
    ad_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaign_ads.id", ondelete="SET NULL"), index=True
    )
    # Who saw it, when the link was opened as a named member of the audience.
    # Null for anonymous preview traffic, and SET NULL if the member is later
    # removed from the list - a deletion must not erase the view it recorded.
    member_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("audience_members.id", ondelete="SET NULL")
    )
    option_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ad_options.id", ondelete="SET NULL")
    )

    # Client-generated per preview session; the deduplication key.
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=utcnow, index=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(255))
    # SHA-256 of IP + server-side salt. The raw address is never stored.
    ip_hash: Mapped[str | None] = mapped_column(String(64))

    campaign = relationship("Campaign", back_populates="events")

    __table_args__ = (
        Index(
            "uniq_view_per_session",
            "campaign_id",
            "session_id",
            unique=True,
            sqlite_where=text("type = 'VIEW'"),
            postgresql_where=text("type = 'VIEW'"),
        ),
        Index(
            "uniq_response_per_session",
            "campaign_id",
            "session_id",
            unique=True,
            sqlite_where=text("type = 'RESPONSE'"),
            postgresql_where=text("type = 'RESPONSE'"),
        ),
        Index("idx_events_campaign_type", "campaign_id", "type"),
        CheckConstraint(
            "(type = 'RESPONSE' AND option_id IS NOT NULL) "
            "OR (type = 'VIEW' AND option_id IS NULL)",
            name="ck_option_required_for_response",
        ),
    )

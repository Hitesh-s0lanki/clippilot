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

    # Denormalised so analytics never joins through experiences to count a view.
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experience_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaign_experiences.id", ondelete="CASCADE")
    )
    recipient_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaign_recipients.id", ondelete="SET NULL")
    )
    option_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaign_options.id", ondelete="SET NULL")
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

"""Recipient (the audience).

The brief carries a single customer name. Modelling it as a row means the
single-customer case is a one-row list, and the optional CSV upload becomes a
bulk insert rather than a rewrite.
"""

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKey


class Recipient(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "campaign_recipients"

    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(20))
    external_ref: Mapped[str | None] = mapped_column(String(120))
    # JSONB on Postgres (binary, indexable, supports containment queries);
    # plain JSON on SQLite, which has no JSONB type.
    attributes: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))

    campaign = relationship("Campaign", back_populates="recipients")

    __table_args__ = (
        # NULLs compare distinct in a unique index on both SQLite and
        # Postgres, so recipients without an email are unconstrained.
        Index("uniq_recipient_email_per_campaign", "campaign_id", "email", unique=True),
    )

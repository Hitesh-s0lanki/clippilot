"""Audience: a reusable, named list of people, and the people in it.

An audience belongs to the account, not to one campaign. That is the whole
point of it - a list is built once, from a CSV or by hand, and then any number
of campaigns select it. A campaign therefore carries a reference to an audience
rather than a private copy of its rows.

The brief's single-customer case survives intact: an audience of one member.
"""

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKey
from src.schemas.enums import Gender


class Audience(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "audiences"

    # Clerk user id, exactly as on Campaign: Clerk owns the user record, so
    # this is a plain string with no foreign key and no local users table.
    owner_user_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    # Denormalised, and recomputed from a COUNT after every membership change
    # rather than incremented. Two reads need it on a path that cannot run a
    # query: the audience listing (which would otherwise be an N+1) and
    # ``collect_publish_blockers``, which is synchronous and called on every
    # campaign read to report whether the campaign can be published.
    member_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    members = relationship(
        "AudienceMember",
        back_populates="audience",
        cascade="all, delete-orphan",
        # Never loaded implicitly. A list can hold thousands of people and
        # almost every read wants a filtered page or an aggregate, not all of
        # them - so membership is always fetched deliberately.
        lazy="noload",
        order_by="AudienceMember.created_at",
    )
    campaigns = relationship("Campaign", back_populates="audience", lazy="noload")

    __table_args__ = (
        # Case-insensitive per owner, the same rule campaign names have.
        Index("uniq_audience_owner_name", "owner_user_id", func.lower(name), unique=True),
    )


class AudienceMember(UUIDPrimaryKey, TimestampMixin, Base):
    """One person in an audience.

    Only ``full_name`` is required - it is what resolves ``{{customer_name}}``.
    Everything else is optional because a real uploaded list is ragged: some
    rows carry an email, some a phone, some neither, and refusing the file over
    a missing cell would be useless.
    """

    __tablename__ = "audience_members"

    audience_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audiences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(20))

    # Segmentation. Age is the number, never the bucket: a stored bucket is
    # wrong the morning after a birthday, and the buckets themselves are a
    # reporting choice that should be free to change.
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=Gender.UNKNOWN.value,
        server_default=Gender.UNKNOWN.value,
    )
    city: Mapped[str | None] = mapped_column(String(80))
    country: Mapped[str | None] = mapped_column(String(56))

    external_ref: Mapped[str | None] = mapped_column(String(120))
    # JSONB on Postgres (binary, indexable, supports containment queries);
    # plain JSON on SQLite, which has no JSONB type.
    attributes: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))

    audience = relationship("Audience", back_populates="members")

    __table_args__ = (
        # Case-insensitive, unlike the index this replaced: an import that
        # dedupes on lowercase and a database that does not is a rule the user
        # sees enforced in one place and not the other. NULLs compare distinct
        # on both SQLite and Postgres, so members with no email are
        # unconstrained.
        Index("uniq_member_email_per_audience", "audience_id", func.lower(email), unique=True),
        # The two columns a segment breakdown groups by most often.
        Index("idx_member_audience_city", "audience_id", "city"),
        Index("idx_member_audience_country", "audience_id", "country"),
    )

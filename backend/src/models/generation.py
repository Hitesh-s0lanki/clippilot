"""AI video generation jobs and their reference assets.

One row per attempt to generate a video from images plus text. Generation is
non-deterministic and slow, so a job is a first-class record rather than a
transient call: the user compares attempts, re-runs a good one by seed, and
only then attaches an output to an ad.

Two decisions worth stating:

* **References are rows, not columns.** ``image_1_url .. image_9_url`` would
  make the model's nine-image ceiling a migration; a child table makes it a
  ``CHECK``. It is the same reasoning that made ``campaign_ads_options`` a
  table rather than ``option_1_*`` columns.
* **The job outlives what it points at.** ``campaign_id`` and ``ad_id`` are
  both nullable with ``SET NULL``: a user may generate before deciding where
  the clip goes, and deleting an ad must not erase the record of what was
  generated or what it cost.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKey
from src.models.types import UTCDateTime
from src.schemas.enums import (
    MAX_CLIP_SECONDS,
    MIN_CLIP_SECONDS,
    GenerationMode,
    GenerationStatus,
    VideoAspectRatio,
    VideoResolution,
)


class GenerationJob(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "generation_jobs"

    # Clerk user id, as everywhere else: Clerk owns the user record.
    owner_user_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), index=True
    )
    # Set on attach, not on submit - the user picks which attempt wins.
    ad_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaign_ads.id", ondelete="SET NULL"), index=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=GenerationStatus.QUEUED.value, index=True
    )
    mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default=GenerationMode.REF2VA.value
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)

    # The provider's own handle: a Modal call_id, or a vendor task id. Indexed
    # because the reconciliation sweep looks jobs up by it.
    provider_job_ref: Mapped[str | None] = mapped_column(String(200), index=True)

    # Exactly what the user typed. Never overwritten - `compiled_prompt` holds
    # what was actually sent, so a bad result can be traced to which of the two
    # was wrong.
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    compiled_prompt: Mapped[str | None] = mapped_column(Text)

    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(
        String(16), nullable=False, default=VideoAspectRatio.NINE_SIXTEEN.value
    )
    resolution: Mapped[str] = mapped_column(
        String(16), nullable=False, default=VideoResolution.P768.value
    )
    # Persisted from the response, not just the request: a result nobody can
    # reproduce is a result nobody can iterate on.
    seed: Mapped[int | None] = mapped_column(BigInteger)
    with_audio: Mapped[bool] = mapped_column(nullable=False, default=True)

    output_video_url: Mapped[str | None] = mapped_column(String(2048))
    output_poster_url: Mapped[str | None] = mapped_column(String(2048))
    # Measured from the file, not echoed from the request.
    output_duration_seconds: Mapped[int | None] = mapped_column(Integer)

    # Minor units, matching campaigns.budget_amount_minor so spend can be
    # summed against a campaign's cap without a unit conversion.
    cost_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(String(3))

    # Stable machine code plus copy that is safe to show the user.
    error_code: Mapped[str | None] = mapped_column(String(60))
    error_message: Mapped[str | None] = mapped_column(String(500))

    # Latency is a product metric here - a two-minute wait needs a progress UI
    # built against real numbers - so all three transitions are recorded.
    queued_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    campaign = relationship("Campaign")
    ad = relationship("Ad")
    assets = relationship(
        "GenerationAsset",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="GenerationAsset.position",
    )

    __table_args__ = (
        CheckConstraint(
            f"duration_seconds BETWEEN {MIN_CLIP_SECONDS} AND {MAX_CLIP_SECONDS}",
            name="ck_generation_duration_range",
        ),
        # The list screen: one owner's jobs, newest first, filtered by status.
        Index("idx_generation_owner_status_created", "owner_user_id", "status", "created_at"),
        # The reconciliation sweep: unfinished jobs, oldest first.
        Index("idx_generation_status_queued", "status", "queued_at"),
    )

    @property
    def is_terminal(self) -> bool:
        from src.schemas.enums import TERMINAL_GENERATION_STATUSES

        return self.status in TERMINAL_GENERATION_STATUSES


class GenerationAsset(UUIDPrimaryKey, TimestampMixin, Base):
    """One reference file handed to the model.

    Stored as rows so the nine-image ceiling is a constraint rather than a
    migration, and so ordering is explicit: ``position`` is what ``<Subject 1>``
    in the compiled prompt refers to.
    """

    __tablename__ = "generation_assets"

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)

    # The label the compiled prompt cites, e.g. "SUBJECT_1". Persisted rather
    # than derived, so re-running an old job cites the same labels even if the
    # builder's naming changes.
    label: Mapped[str] = mapped_column(String(40), nullable=False)

    # The user's own words for what must not change about this reference.
    # This is the highest-leverage field on the form: it becomes the prompt's
    # retention_analysis, which is what keeps a product recognisable.
    subject_note: Mapped[str | None] = mapped_column(String(200))

    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Only meaningful for video and audio, which the model bounds to 2-15s.
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    job = relationship("GenerationJob", back_populates="assets")

    __table_args__ = (Index("uniq_generation_asset_position", "job_id", "position", unique=True),)

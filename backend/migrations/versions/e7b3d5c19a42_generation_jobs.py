"""generation jobs: AI video generation from images plus text

Two tables behind the feature that fills an ad's ``video_url`` with a generated
file rather than an uploaded one.

``generation_jobs`` is a record, not a transient call. Generation is slow and
non-deterministic, so the user compares attempts and re-runs a good one by
seed; the row keeps the prompt actually sent, the seed, the cost and the
timings that a two-minute progress UI has to be built against.

``generation_assets`` holds the references as rows. ``image_1_url ..
image_9_url`` would make the model's nine-image ceiling a migration; a child
table makes it a constraint - the same reasoning behind ``campaign_ad_options``.

Both foreign keys are nullable with SET NULL: a user may generate before
choosing where the clip goes, and deleting an ad must not erase the record of
what was generated or what it cost.

Revision ID: e7b3d5c19a42
Revises: c4d2f8a91b37
Create Date: 2026-08-23 19:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7b3d5c19a42"
down_revision: str | Sequence[str] | None = "c4d2f8a91b37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("campaign_id", sa.String(length=36), nullable=True),
        sa.Column("ad_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_job_ref", sa.String(length=200), nullable=True),
        sa.Column("user_prompt", sa.Text(), nullable=False),
        sa.Column("compiled_prompt", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=16), nullable=False),
        sa.Column("resolution", sa.String(length=16), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=True),
        sa.Column("with_audio", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("output_video_url", sa.String(length=2048), nullable=True),
        sa.Column("output_poster_url", sa.String(length=2048), nullable=True),
        sa.Column("output_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("cost_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("error_code", sa.String(length=60), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "duration_seconds BETWEEN 4 AND 15", name="ck_generation_duration_range"
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ad_id"], ["campaign_ads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generation_jobs_owner_user_id", "generation_jobs", ["owner_user_id"], unique=False
    )
    op.create_index("ix_generation_jobs_campaign_id", "generation_jobs", ["campaign_id"])
    op.create_index("ix_generation_jobs_ad_id", "generation_jobs", ["ad_id"])
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"])
    op.create_index("ix_generation_jobs_provider_job_ref", "generation_jobs", ["provider_job_ref"])
    # The list screen: one owner's jobs, newest first, filtered by status.
    op.create_index(
        "idx_generation_owner_status_created",
        "generation_jobs",
        ["owner_user_id", "status", "created_at"],
    )
    # The reconciliation sweep: unfinished jobs, oldest first.
    op.create_index("idx_generation_status_queued", "generation_jobs", ["status", "queued_at"])

    op.create_table(
        "generation_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=40), nullable=False),
        sa.Column("subject_note", sa.String(length=200), nullable=True),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["generation_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_assets_job_id", "generation_assets", ["job_id"])
    op.create_index(
        "uniq_generation_asset_position", "generation_assets", ["job_id", "position"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uniq_generation_asset_position", table_name="generation_assets")
    op.drop_index("ix_generation_assets_job_id", table_name="generation_assets")
    op.drop_table("generation_assets")

    for name in (
        "idx_generation_status_queued",
        "idx_generation_owner_status_created",
        "ix_generation_jobs_provider_job_ref",
        "ix_generation_jobs_status",
        "ix_generation_jobs_ad_id",
        "ix_generation_jobs_campaign_id",
        "ix_generation_jobs_owner_user_id",
    ):
        op.drop_index(name, table_name="generation_jobs")
    op.drop_table("generation_jobs")

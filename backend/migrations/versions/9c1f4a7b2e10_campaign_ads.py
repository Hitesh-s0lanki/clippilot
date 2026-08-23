"""experiences become ads: 1:N, with their own status, description and CTA

Renames ``campaign_experiences`` to ``campaign_ads`` and promotes it from a
single creative per campaign to a real one-to-many child, in the shape of a
Meta ad: its own ``name``, its own ``status``, recipient-facing ``description``
and a ``cta``.

``campaign_options`` follows it to ``ad_options`` with ``experience_id`` renamed
to ``ad_id``, and ``campaign_events.experience_id`` becomes ``ad_id`` - now with
ON DELETE SET NULL rather than CASCADE, so deleting one creative no longer
erases the campaign's view history.

Existing rows are preserved. Every experience becomes an ad named after its
campaign and carrying that campaign's status, which is the only interpretation
that keeps a live campaign live through the upgrade.

Revision ID: 9c1f4a7b2e10
Revises: 581afeb93402
Create Date: 2026-08-23 12:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c1f4a7b2e10"
down_revision: str | Sequence[str] | None = "581afeb93402"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- campaign_experiences -> campaign_ads ------------------------------
    op.rename_table("campaign_experiences", "campaign_ads")

    with op.batch_alter_table("campaign_ads", schema=None) as batch_op:
        batch_op.drop_index("ix_campaign_experiences_campaign_id")
        # Added nullable, backfilled below, then made NOT NULL: a new NOT NULL
        # column with no default cannot be added to a table that has rows.
        batch_op.add_column(sa.Column("name", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("description", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("cta", sa.String(length=32), nullable=True))

    # An existing experience is its campaign's only creative, so it inherits
    # the campaign's name and status. Anything else would either collide on
    # the new unique index or silently take a live campaign off the air.
    op.execute(
        """
        UPDATE campaign_ads
        SET name = (SELECT c.name FROM campaigns c WHERE c.id = campaign_ads.campaign_id)
        WHERE name IS NULL
        """
    )
    op.execute(
        """
        UPDATE campaign_ads
        SET status = (SELECT c.status FROM campaigns c WHERE c.id = campaign_ads.campaign_id)
        WHERE status IS NULL
        """
    )
    # Campaign statuses an ad has no equivalent for collapse to the nearest
    # ad status: anything scheduled or finished is simply not running yet.
    op.execute("UPDATE campaign_ads SET status = 'ACTIVE' WHERE status IN ('SCHEDULED')")
    op.execute("UPDATE campaign_ads SET status = 'PAUSED' WHERE status IN ('COMPLETED')")
    op.execute("UPDATE campaign_ads SET status = 'DRAFT' WHERE status IS NULL")
    op.execute("UPDATE campaign_ads SET name = 'Ad 1' WHERE name IS NULL OR name = ''")
    op.execute("UPDATE campaign_ads SET cta = 'LEARN_MORE' WHERE cta IS NULL")

    with op.batch_alter_table("campaign_ads", schema=None) as batch_op:
        batch_op.alter_column("name", existing_type=sa.String(length=120), nullable=False)
        batch_op.alter_column("status", existing_type=sa.String(length=32), nullable=False)
        batch_op.alter_column("cta", existing_type=sa.String(length=32), nullable=False)
        batch_op.create_index("ix_campaign_ads_campaign_id", ["campaign_id"], unique=False)
        batch_op.create_index("ix_campaign_ads_status", ["status"], unique=False)
        batch_op.create_index("idx_ad_campaign_status", ["campaign_id", "status"], unique=False)

    # Functional index - autogenerate cannot see these, so it is explicit.
    op.execute(
        "CREATE UNIQUE INDEX uniq_ad_name_per_campaign ON campaign_ads (campaign_id, lower(name))"
    )

    # --- campaign_options -> ad_options ------------------------------------
    op.rename_table("campaign_options", "ad_options")

    with op.batch_alter_table("ad_options", schema=None) as batch_op:
        batch_op.drop_index("uniq_option_position")
        batch_op.drop_index("uniq_option_key")
        batch_op.drop_index("ix_campaign_options_experience_id")
        batch_op.alter_column(
            "experience_id", new_column_name="ad_id", existing_type=sa.String(length=36)
        )

    with op.batch_alter_table("ad_options", schema=None) as batch_op:
        batch_op.create_index("ix_ad_options_ad_id", ["ad_id"], unique=False)
        batch_op.create_index("uniq_option_position", ["ad_id", "position"], unique=True)
        batch_op.create_index("uniq_option_key", ["ad_id", "key"], unique=True)

    # --- campaign_events.experience_id -> ad_id ----------------------------
    with op.batch_alter_table("campaign_events", schema=None) as batch_op:
        batch_op.alter_column(
            "experience_id", new_column_name="ad_id", existing_type=sa.String(length=36)
        )

    with op.batch_alter_table("campaign_events", schema=None) as batch_op:
        batch_op.create_index("ix_campaign_events_ad_id", ["ad_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema.

    ``name``, ``status``, ``description`` and ``cta`` are dropped, and any
    campaign holding more than one ad loses all but the first - the old schema
    had nowhere to put them.
    """
    with op.batch_alter_table("campaign_events", schema=None) as batch_op:
        batch_op.drop_index("ix_campaign_events_ad_id")
        batch_op.alter_column(
            "ad_id", new_column_name="experience_id", existing_type=sa.String(length=36)
        )

    with op.batch_alter_table("ad_options", schema=None) as batch_op:
        batch_op.drop_index("uniq_option_key")
        batch_op.drop_index("uniq_option_position")
        batch_op.drop_index("ix_ad_options_ad_id")
        batch_op.alter_column(
            "ad_id", new_column_name="experience_id", existing_type=sa.String(length=36)
        )

    with op.batch_alter_table("ad_options", schema=None) as batch_op:
        batch_op.create_index("ix_campaign_options_experience_id", ["experience_id"], unique=False)
        batch_op.create_index("uniq_option_position", ["experience_id", "position"], unique=True)
        batch_op.create_index("uniq_option_key", ["experience_id", "key"], unique=True)

    op.rename_table("ad_options", "campaign_options")

    op.execute("DROP INDEX IF EXISTS uniq_ad_name_per_campaign")

    # Keep only the oldest ad per campaign; the old schema holds exactly one.
    op.execute(
        """
        DELETE FROM campaign_ads
        WHERE id NOT IN (
            SELECT MIN(id) FROM campaign_ads GROUP BY campaign_id
        )
        """
    )

    with op.batch_alter_table("campaign_ads", schema=None) as batch_op:
        batch_op.drop_index("idx_ad_campaign_status")
        batch_op.drop_index("ix_campaign_ads_status")
        batch_op.drop_index("ix_campaign_ads_campaign_id")
        batch_op.drop_column("cta")
        batch_op.drop_column("description")
        batch_op.drop_column("status")
        batch_op.drop_column("name")

    op.rename_table("campaign_ads", "campaign_experiences")

    with op.batch_alter_table("campaign_experiences", schema=None) as batch_op:
        batch_op.create_index("ix_campaign_experiences_campaign_id", ["campaign_id"], unique=False)

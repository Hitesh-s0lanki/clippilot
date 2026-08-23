"""recipients become audiences: reusable lists a campaign selects

``campaign_recipients`` was a private column of one campaign. It becomes two
tables the account owns - ``audiences`` and ``audience_members`` - and the
campaign keeps a reference to one of them instead of a copy of its rows. That
is what lets the same list run several campaigns, and what gives the segment
breakdown something to aggregate over.

Members gain the fields a breakdown needs: ``age``, ``gender``, ``city`` and
``country``. ``customer_name`` becomes ``full_name`` - the ``{{customer_name}}``
merge tag keeps its spelling, only the column behind it is renamed.

Existing rows are preserved. Every campaign that had recipients gets an
audience of its own named after it, so a live campaign stays live and its
personalisation resolves exactly as before. ``campaign_events.recipient_id``
follows to ``member_id`` with the ids remapped, so recorded views keep pointing
at the person who made them.

``campaigns.audience_type`` is dropped: SINGLE vs LIST was a statement about how
many rows the campaign carried, and a campaign no longer carries any - the
audience's own size says it.

Revision ID: c4d2f8a91b37
Revises: 9c1f4a7b2e10
Create Date: 2026-08-23 18:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4d2f8a91b37"
down_revision: str | Sequence[str] | None = "9c1f4a7b2e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# SQLite's batch mode reflects the table it is about to copy, and a foreign key
# the initial migration left unnamed comes back unnamed. Supplying a convention
# gives it a deterministic name so it can be dropped.
FK_NAMING_CONVENTION = {"fk": "fk_%(table_name)s_%(column_0_name)s"}


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    json_type = sa.dialects.postgresql.JSONB if bind.dialect.name == "postgresql" else sa.JSON

    # --- the two new tables ------------------------------------------------
    op.create_table(
        "audiences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("member_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audiences_owner_user_id", "audiences", ["owner_user_id"], unique=False)
    # Functional, so autogenerate cannot see it and it has to be written out.
    op.execute(
        "CREATE UNIQUE INDEX uniq_audience_owner_name ON audiences (owner_user_id, lower(name))"
    )

    op.create_table(
        "audience_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("audience_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=16), server_default="UNKNOWN", nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("country", sa.String(length=56), nullable=True),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("attributes", json_type(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["audience_id"], ["audiences.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audience_members_audience_id", "audience_members", ["audience_id"], unique=False
    )
    op.create_index(
        "idx_member_audience_city", "audience_members", ["audience_id", "city"], unique=False
    )
    op.create_index(
        "idx_member_audience_country", "audience_members", ["audience_id", "country"], unique=False
    )
    op.execute(
        "CREATE UNIQUE INDEX uniq_member_email_per_audience "
        "ON audience_members (audience_id, lower(email))"
    )

    # --- campaigns point at one ---------------------------------------------
    with op.batch_alter_table("campaigns", schema=None) as batch_op:
        batch_op.add_column(sa.Column("audience_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_campaigns_audience_id", ["audience_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_campaigns_audience_id", "audiences", ["audience_id"], ["id"], ondelete="SET NULL"
        )

    # --- move the data ------------------------------------------------------
    # One audience per campaign that had anybody, reusing the campaign's own id
    # so the mapping back to its members needs no lookup table. The name is the
    # campaign's, which is both recognisable and unique per owner already.
    op.execute(
        """
        INSERT INTO audiences (id, owner_user_id, name, description, member_count,
                               created_at, updated_at)
        SELECT c.id,
               c.owner_user_id,
               c.name,
               'Moved from the campaign that used to carry these people.',
               (SELECT COUNT(*) FROM campaign_recipients r WHERE r.campaign_id = c.id),
               c.created_at,
               c.updated_at
        FROM campaigns c
        WHERE EXISTS (SELECT 1 FROM campaign_recipients r WHERE r.campaign_id = c.id)
        """
    )

    # Member ids are carried over from the recipient rows, which is what keeps
    # campaign_events.recipient_id meaningful through the rename below.
    op.execute(
        """
        INSERT INTO audience_members (id, audience_id, full_name, email, phone, age, gender,
                                      city, country, external_ref, attributes,
                                      created_at, updated_at)
        SELECT r.id, r.campaign_id, r.customer_name, r.email, r.phone, NULL, 'UNKNOWN',
               NULL, NULL, r.external_ref, r.attributes, r.created_at, r.updated_at
        FROM campaign_recipients r
        """
    )

    op.execute(
        """
        UPDATE campaigns
        SET audience_id = id
        WHERE EXISTS (SELECT 1 FROM audience_members m WHERE m.audience_id = campaigns.id)
        """
    )

    # --- events follow ------------------------------------------------------
    # The ids did not change, so renaming the column is most of the remap. The
    # foreign key has to move with it: it still names campaign_recipients,
    # which is dropped a few lines below. PostgreSQL refuses that DROP TABLE
    # while the constraint exists, and SQLite would allow it and leave the
    # column pointing at a table that is gone.
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE campaign_events RENAME COLUMN recipient_id TO member_id")
        # The initial migration left this constraint unnamed, so the name here
        # is the one PostgreSQL generated for it.
        op.execute(
            "ALTER TABLE campaign_events "
            "DROP CONSTRAINT IF EXISTS campaign_events_recipient_id_fkey"
        )
        op.create_foreign_key(
            "fk_campaign_events_member_id",
            "campaign_events",
            "audience_members",
            ["member_id"],
            ["id"],
            ondelete="SET NULL",
        )
    else:
        # SQLite has no ALTER for constraints, so batch mode copies the table.
        # naming_convention is what lets that unnamed, reflected foreign key be
        # addressed by name at all. The new key needs a second block: a foreign
        # key added in the same block as the rename that creates its column is
        # dropped from the copy without a word.
        with op.batch_alter_table(
            "campaign_events", schema=None, naming_convention=FK_NAMING_CONVENTION
        ) as batch_op:
            batch_op.drop_constraint("fk_campaign_events_recipient_id", type_="foreignkey")
            batch_op.alter_column(
                "recipient_id", new_column_name="member_id", existing_type=sa.String(length=36)
            )

        with op.batch_alter_table(
            "campaign_events", schema=None, naming_convention=FK_NAMING_CONVENTION
        ) as batch_op:
            batch_op.create_foreign_key(
                "fk_campaign_events_member_id",
                "audience_members",
                ["member_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # --- retire the old table ----------------------------------------------
    op.execute("DROP INDEX IF EXISTS uniq_recipient_email_per_campaign")
    op.drop_index("ix_campaign_recipients_campaign_id", table_name="campaign_recipients")
    op.drop_table("campaign_recipients")

    with op.batch_alter_table("campaigns", schema=None) as batch_op:
        batch_op.drop_column("audience_type")


def downgrade() -> None:
    """Downgrade schema.

    Every campaign gets back the members of the audience it selected. Age,
    gender, city and country are dropped - the old table had nowhere to put
    them - and an audience no campaign selected is lost with them, since a
    recipient row cannot exist without a campaign to hang off.
    """
    bind = op.get_bind()
    json_type = sa.dialects.postgresql.JSONB if bind.dialect.name == "postgresql" else sa.JSON

    op.create_table(
        "campaign_recipients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.String(length=36), nullable=False),
        sa.Column("customer_name", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("attributes", json_type(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_campaign_recipients_campaign_id", "campaign_recipients", ["campaign_id"], unique=False
    )
    op.execute(
        "CREATE UNIQUE INDEX uniq_recipient_email_per_campaign "
        "ON campaign_recipients (campaign_id, email)"
    )

    with op.batch_alter_table("campaigns", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "audience_type", sa.String(length=16), server_default="SINGLE", nullable=False
            )
        )

    # A member selected by two campaigns becomes a row under each: the ids can
    # only follow one of them, so the first campaign keeps them and the rest
    # get fresh ones. Events therefore stay attached to that first campaign.
    op.execute(
        """
        INSERT INTO campaign_recipients (id, campaign_id, customer_name, email, phone,
                                         external_ref, attributes, created_at, updated_at)
        SELECT m.id, c.id, m.full_name, m.email, m.phone, m.external_ref, m.attributes,
               m.created_at, m.updated_at
        FROM audience_members m
        JOIN campaigns c ON c.audience_id = m.audience_id
        WHERE c.id = (
            SELECT MIN(c2.id) FROM campaigns c2 WHERE c2.audience_id = m.audience_id
        )
        """
    )

    op.execute(
        """
        UPDATE campaigns
        SET audience_type = 'LIST'
        WHERE (SELECT COUNT(*) FROM campaign_recipients r WHERE r.campaign_id = campaigns.id) > 1
        """
    )

    # The mirror image of the upgrade: the foreign key goes back to
    # campaign_recipients before audience_members is dropped below.
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_campaign_events_member_id", "campaign_events", type_="foreignkey")
        op.execute("ALTER TABLE campaign_events RENAME COLUMN member_id TO recipient_id")
        op.create_foreign_key(
            "campaign_events_recipient_id_fkey",
            "campaign_events",
            "campaign_recipients",
            ["recipient_id"],
            ["id"],
            ondelete="SET NULL",
        )
    else:
        with op.batch_alter_table(
            "campaign_events", schema=None, naming_convention=FK_NAMING_CONVENTION
        ) as batch_op:
            batch_op.drop_constraint("fk_campaign_events_member_id", type_="foreignkey")
            batch_op.alter_column(
                "member_id", new_column_name="recipient_id", existing_type=sa.String(length=36)
            )

        with op.batch_alter_table(
            "campaign_events", schema=None, naming_convention=FK_NAMING_CONVENTION
        ) as batch_op:
            batch_op.create_foreign_key(
                "campaign_events_recipient_id_fkey",
                "campaign_recipients",
                ["recipient_id"],
                ["id"],
                ondelete="SET NULL",
            )

    with op.batch_alter_table("campaigns", schema=None) as batch_op:
        batch_op.drop_constraint("fk_campaigns_audience_id", type_="foreignkey")
        batch_op.drop_index("ix_campaigns_audience_id")
        batch_op.drop_column("audience_id")

    op.execute("DROP INDEX IF EXISTS uniq_member_email_per_audience")
    op.drop_index("idx_member_audience_country", table_name="audience_members")
    op.drop_index("idx_member_audience_city", table_name="audience_members")
    op.drop_index("ix_audience_members_audience_id", table_name="audience_members")
    op.drop_table("audience_members")

    op.execute("DROP INDEX IF EXISTS uniq_audience_owner_name")
    op.drop_index("ix_audiences_owner_user_id", table_name="audiences")
    op.drop_table("audiences")

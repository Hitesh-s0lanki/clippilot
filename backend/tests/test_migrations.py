"""Guards that the migrations stay in step with the ORM metadata.

These are static checks over the migration source, so they run on every
engine and need no database. They exist because Alembic's autogenerate does
not detect functional indexes: ``uniq_campaign_owner_name`` was silently
absent from the initial migration, which would have left campaign-name
uniqueness unenforced on any database built from migrations.
"""

from pathlib import Path

import pytest

import src.models  # noqa: F401 - populates Base.metadata
from src.core.database import Base

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations" / "versions"


@pytest.fixture(scope="module")
def migration_source() -> str:
    files = sorted(MIGRATIONS.glob("*.py"))
    assert files, "no migration files found"
    return "\n".join(f.read_text() for f in files)


def _metadata_index_names() -> set[str]:
    return {
        index.name
        for table in Base.metadata.tables.values()
        for index in table.indexes
        if index.name
    }


def _metadata_constraint_names() -> set[str]:
    names: set[str] = set()
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if constraint.name and str(constraint.name) != "_unnamed_":
                names.add(str(constraint.name))
    return names


class TestMigrationParity:
    def test_every_declared_index_appears_in_a_migration(self, migration_source: str) -> None:
        missing = sorted(name for name in _metadata_index_names() if name not in migration_source)

        assert not missing, (
            f"Indexes declared on the models but absent from migrations: {missing}. "
            "Autogenerate cannot see functional indexes - add them with op.execute()."
        )

    def test_every_named_check_constraint_appears_in_a_migration(
        self, migration_source: str
    ) -> None:
        declared = {n for n in _metadata_constraint_names() if n.startswith("ck_")}

        missing = sorted(name for name in declared if name not in migration_source)

        assert not missing, f"Check constraints absent from migrations: {missing}"

    def test_every_table_appears_in_a_migration(self, migration_source: str) -> None:
        missing = sorted(name for name in Base.metadata.tables if name not in migration_source)

        assert not missing, f"Tables absent from migrations: {missing}"

    def test_the_functional_uniqueness_index_is_explicit(self, migration_source: str) -> None:
        # The specific omission this module was written for.
        assert "uniq_campaign_owner_name" in migration_source
        assert "lower(name)" in migration_source

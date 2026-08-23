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


class TestStartupSchemaGuard:
    """`create_all` must never run against a database Alembic already owns.

    The bug this guards: `create_all` adds missing tables and silently leaves
    existing ones alone, so a stale SQLite file gains the new tables (empty)
    while an existing table keeps missing the column the ORM now expects. The
    first query fails with `no such column`, a long way from the cause.
    """

    def test_a_fresh_file_is_created_from_the_metadata(self, tmp_path: Path) -> None:
        from sqlalchemy import create_engine, inspect

        from src.main import _prepare_sqlite_schema

        engine = create_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
        with engine.begin() as connection:
            _prepare_sqlite_schema(connection)

        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())

        assert {"campaigns", "campaign_ads", "ad_options", "audiences"} <= tables

    def test_a_database_behind_head_is_refused(self, tmp_path: Path) -> None:
        from sqlalchemy import create_engine

        from src.main import _prepare_sqlite_schema

        engine = create_engine(f"sqlite:///{tmp_path / 'stale.db'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32))")
            connection.exec_driver_sql("INSERT INTO alembic_version VALUES ('581afeb93402')")

        with pytest.raises(RuntimeError, match="alembic upgrade head"), engine.begin() as conn:
            _prepare_sqlite_schema(conn)

    def test_a_database_at_head_is_left_alone(self, tmp_path: Path) -> None:
        from alembic.script import ScriptDirectory
        from sqlalchemy import create_engine, inspect

        from src.main import MIGRATIONS_DIR, _prepare_sqlite_schema

        head = ScriptDirectory(str(MIGRATIONS_DIR)).get_current_head()
        engine = create_engine(f"sqlite:///{tmp_path / 'current.db'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32))")
            connection.exec_driver_sql(f"INSERT INTO alembic_version VALUES ('{head}')")

        with engine.begin() as connection:
            _prepare_sqlite_schema(connection)

        # Nothing invented: a migration-managed database is Alembic's to build.
        with engine.connect() as connection:
            assert inspect(connection).get_table_names() == ["alembic_version"]

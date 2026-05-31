import os
import re

import psycopg
import pytest
from pytest_postgresql import factories

_INIT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "init"))

_SCHEMA_FILES = [
    "01_schema.sql",
    "01_create_clue_schema.sql",
    "02_views.sql",
    "02_create_helper_functions.sql",
    "03_create_processing_procedure.sql",
    "03_create_processing_procedure_v2.sql",
]
_SEED_FILE = "10_seed_roles.sql"


def _strip_metacommands(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines()
        if not line.strip().startswith("\\")
    )


def _split_statements(sql: str) -> list[str]:
    """Split SQL into individual statements, respecting $$ dollar-quoted blocks."""
    statements: list[str] = []
    current: list[str] = []
    i = 0
    n = len(sql)
    in_dollar_quote = False
    dollar_tag = ""

    while i < n:
        if sql[i] == "$":
            m = re.match(r"\$[^$]*\$", sql[i:])
            if m:
                tag = m.group(0)
                if not in_dollar_quote:
                    in_dollar_quote = True
                    dollar_tag = tag
                    current.append(tag)
                    i += len(tag)
                    continue
                elif tag == dollar_tag:
                    in_dollar_quote = False
                    current.append(tag)
                    i += len(tag)
                    continue

        if sql[i] == ";" and not in_dollar_quote:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(sql[i])
        i += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def _exec_file(conn: psycopg.Connection, path: str) -> None:
    with open(path) as fh:
        sql = _strip_metacommands(fh.read())
    with conn.cursor() as cur:
        for stmt in _split_statements(sql):
            cur.execute(stmt)
    conn.commit()


def _bootstrap(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
        cur.execute(
            """
            DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'metadata_admin') THEN
                CREATE ROLE metadata_admin LOGIN PASSWORD 'metadata_admin';
              END IF;
            END $$
            """
        )
    conn.commit()
    for filename in _SCHEMA_FILES:
        _exec_file(conn, os.path.join(_INIT_DIR, filename))


postgresql_proc = factories.postgresql_proc(port=None)
postgresql = factories.postgresql("postgresql_proc")


@pytest.fixture
def db_clean(postgresql):
    """Fresh DB with schema only. Use for write/constraint tests."""
    _bootstrap(postgresql)
    return postgresql


@pytest.fixture
def db(postgresql):
    """Fresh DB with schema + seed data. Use for read-only tests."""
    _bootstrap(postgresql)
    _exec_file(postgresql, os.path.join(_INIT_DIR, _SEED_FILE))
    return postgresql

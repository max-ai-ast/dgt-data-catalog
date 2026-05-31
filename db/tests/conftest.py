import os

import psycopg2
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


def _exec_file(conn, path: str) -> None:
    with open(path) as fh:
        sql = _strip_metacommands(fh.read())
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def _bootstrap(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    conn.commit()
    for filename in _SCHEMA_FILES:
        _exec_file(conn, os.path.join(_INIT_DIR, filename))


postgresql_proc = factories.postgresql_proc(port=None, scope="session")
_postgresql_session = factories.postgresql("postgresql_proc", scope="session")
_postgresql_fn = factories.postgresql("postgresql_proc")


@pytest.fixture(scope="session")
def db(_postgresql_session):
    """Session-scoped DB with schema + seed data. Use for read-only tests."""
    _bootstrap(_postgresql_session)
    _exec_file(_postgresql_session, os.path.join(_INIT_DIR, _SEED_FILE))
    return _postgresql_session


@pytest.fixture
def db_clean(_postgresql_fn):
    """Function-scoped DB with schema only. Use for tests that write data."""
    _bootstrap(_postgresql_fn)
    return _postgresql_fn


@pytest.fixture
def db_txn(db):
    """Wraps each test in a savepoint against the session DB; rolls back after."""
    with db.cursor() as cur:
        cur.execute("SAVEPOINT test_sp")
    yield db
    with db.cursor() as cur:
        cur.execute("ROLLBACK TO SAVEPOINT test_sp")
        cur.execute("RELEASE SAVEPOINT test_sp")
    db.commit()

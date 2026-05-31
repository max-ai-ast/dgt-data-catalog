import pytest

_PUBLIC_TABLES = [
    "agency",
    "dataset",
    "distribution",
    "tag",
    "dataset_tag",
    "policy",
    "policy_clause",
    "dataset_policy",
    "permissible_use",
    "permissible_use_condition",
    "security_marking",
    "dataset_security_marking",
    "governance_role",
    "person",
    "role_assignment",
    "decision_log",
    "data_access_request",
    "dataset_lineage",
    "glossary_term",
]

_CLUE_TABLES = [
    "file_load_metadata",
    "source_data",
    "cases",
    "defendants",
    "plaintiffs",
    "case_types",
]


def _table_exists(conn, schema: str, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            )
            """,
            (schema, table),
        )
        return cur.fetchone()[0]


@pytest.mark.parametrize("table", _PUBLIC_TABLES)
def test_public_table_exists(db, table):
    assert _table_exists(db, "public", table)


@pytest.mark.parametrize("table", _CLUE_TABLES)
def test_clue_table_exists(db, table):
    assert _table_exists(db, "clue", table)


def test_dataset_is_sensitive_defaults_false(db_clean):
    with db_clean.cursor() as cur:
        cur.execute(
            "INSERT INTO dataset (title, source_identifier) VALUES ('DS', 'test-1') RETURNING is_sensitive"
        )
        assert cur.fetchone()[0] is False


def test_dataset_source_identifier_unique(db_clean):
    with db_clean.cursor() as cur:
        cur.execute(
            "INSERT INTO dataset (title, source_identifier) VALUES ('DS1', 'dup-id')"
        )
    db_clean.commit()

    with pytest.raises(Exception):
        with db_clean.cursor() as cur:
            cur.execute(
                "INSERT INTO dataset (title, source_identifier) VALUES ('DS2', 'dup-id')"
            )

    db_clean.rollback()


def test_agency_name_case_insensitive_unique(db_clean):
    with db_clean.cursor() as cur:
        cur.execute("INSERT INTO agency (name) VALUES ('Test Agency')")
    db_clean.commit()

    with pytest.raises(Exception):
        with db_clean.cursor() as cur:
            cur.execute("INSERT INTO agency (name) VALUES ('test agency')")

    db_clean.rollback()


def test_distribution_cascades_on_dataset_delete(db_clean):
    with db_clean.cursor() as cur:
        cur.execute(
            "INSERT INTO dataset (title, source_identifier) VALUES ('CascadeDS', 'cascade-1') RETURNING dataset_id"
        )
        ds_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO distribution (dataset_id) VALUES (%s) RETURNING distribution_id",
            (ds_id,),
        )
        dist_id = cur.fetchone()[0]
    db_clean.commit()

    with db_clean.cursor() as cur:
        cur.execute("DELETE FROM dataset WHERE dataset_id = %s", (ds_id,))
    db_clean.commit()

    with db_clean.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM distribution WHERE distribution_id = %s", (dist_id,)
        )
        assert cur.fetchone() is None


def test_role_assignment_scope_defaults_enterprise(db_clean):
    with db_clean.cursor() as cur:
        cur.execute(
            "INSERT INTO governance_role (name) VALUES ('Test Role') RETURNING governance_role_id"
        )
        role_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO person (full_name) VALUES ('Test Person') RETURNING person_id"
        )
        person_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO role_assignment (governance_role_id, person_id) VALUES (%s, %s) RETURNING scope",
            (role_id, person_id),
        )
        assert cur.fetchone()[0] == "enterprise"


def test_tag_name_type_unique(db_clean):
    with db_clean.cursor() as cur:
        cur.execute("INSERT INTO tag (name, tag_type) VALUES ('env', 'keyword')")
    db_clean.commit()

    with pytest.raises(Exception):
        with db_clean.cursor() as cur:
            cur.execute("INSERT INTO tag (name, tag_type) VALUES ('ENV', 'keyword')")

    db_clean.rollback()

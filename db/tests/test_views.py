import pytest

_VIEWS = [
    "vw_catalog_dataset",
    "vw_permissible_use",
    "vw_governance_assignments",
    "vw_data_access_request",
]

_CATALOG_COLUMNS = {
    "dataset_id",
    "title",
    "description",
    "source_identifier",
    "agency_name",
    "agency_acronym",
    "landing_page",
    "license",
    "public_access_level",
    "is_sensitive",
    "tags",
    "security_markings",
    "policies",
}

_PERMISSIBLE_USE_COLUMNS = {
    "permissible_use_id",
    "policy_id",
    "policy_name",
    "use_case",
    "description",
    "requires_approval",
    "approval_authority",
    "conditions",
}

_GOVERNANCE_ASSIGNMENT_COLUMNS = {
    "role_assignment_id",
    "role_name",
    "role_description",
    "responsibilities",
    "scope",
    "full_name",
    "email",
    "organization",
    "dataset_id",
    "dataset_title",
}

_ACCESS_REQUEST_COLUMNS = {
    "request_id",
    "dataset_id",
    "dataset_title",
    "requested_by",
    "requested_on",
    "purpose",
    "status",
    "decision_type",
    "decision_text",
    "decided_by",
    "decided_on",
}


def _col_names(cursor) -> set:
    return {desc[0] for desc in cursor.description}


@pytest.mark.parametrize("view", _VIEWS)
def test_view_is_selectable(db, view):
    with db.cursor() as cur:
        cur.execute(f"SELECT * FROM {view} LIMIT 0")
        assert cur.description is not None


def test_catalog_dataset_columns(db):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM vw_catalog_dataset LIMIT 0")
        assert _CATALOG_COLUMNS.issubset(_col_names(cur))


def test_permissible_use_columns(db):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM vw_permissible_use LIMIT 0")
        assert _PERMISSIBLE_USE_COLUMNS.issubset(_col_names(cur))


def test_governance_assignments_columns(db):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM vw_governance_assignments LIMIT 0")
        assert _GOVERNANCE_ASSIGNMENT_COLUMNS.issubset(_col_names(cur))


def test_data_access_request_columns(db):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM vw_data_access_request LIMIT 0")
        assert _ACCESS_REQUEST_COLUMNS.issubset(_col_names(cur))


def test_catalog_dataset_aggregates_tags(db_txn):
    with db_txn.cursor() as cur:
        cur.execute(
            "INSERT INTO agency (name, acronym) VALUES ('Agg Agency', 'AA') RETURNING agency_id"
        )
        agency_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO dataset (title, source_identifier, agency_id) VALUES ('Tagged DS', 'tag-agg-1', %s) RETURNING dataset_id",
            (agency_id,),
        )
        ds_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO tag (name, tag_type) VALUES ('climate', 'keyword') RETURNING tag_id"
        )
        tag_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO dataset_tag (dataset_id, tag_id, tag_source) VALUES (%s, %s, 'data_gov')",
            (ds_id, tag_id),
        )

        cur.execute(
            "SELECT tags FROM vw_catalog_dataset WHERE dataset_id = %s", (ds_id,)
        )
        row = cur.fetchone()
        assert row is not None
        assert "climate" in row[0]


def test_catalog_dataset_aggregates_security_markings(db_txn):
    with db_txn.cursor() as cur:
        cur.execute(
            "INSERT INTO dataset (title, source_identifier) VALUES ('Marked DS', 'mark-agg-1') RETURNING dataset_id"
        )
        ds_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO security_marking (name, classification_level) VALUES ('FOUO', 'moderate') RETURNING security_marking_id"
        )
        sm_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO dataset_security_marking (dataset_id, security_marking_id) VALUES (%s, %s)",
            (ds_id, sm_id),
        )

        cur.execute(
            "SELECT security_markings FROM vw_catalog_dataset WHERE dataset_id = %s",
            (ds_id,),
        )
        row = cur.fetchone()
        assert row is not None
        assert "FOUO" in row[0]


def test_catalog_dataset_no_policy_returns_empty_array(db_txn):
    with db_txn.cursor() as cur:
        cur.execute(
            "INSERT INTO dataset (title, source_identifier) VALUES ('No Policy DS', 'nopol-1') RETURNING dataset_id"
        )
        ds_id = cur.fetchone()[0]

        cur.execute(
            "SELECT policies FROM vw_catalog_dataset WHERE dataset_id = %s", (ds_id,)
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == []


def test_permissible_use_conditions_is_jsonb_array(db):
    with db.cursor() as cur:
        cur.execute("SELECT conditions FROM vw_permissible_use LIMIT 1")
        row = cur.fetchone()
        if row is not None:
            assert row[0] is None or isinstance(row[0], list)


def test_governance_assignments_joins_person_and_role(db_txn):
    with db_txn.cursor() as cur:
        cur.execute(
            "INSERT INTO governance_role (name, description) VALUES ('Auditor', 'Audits data') RETURNING governance_role_id"
        )
        role_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO person (full_name, email, organization) VALUES ('Jane Doe', 'jane@example.com', 'DGT') RETURNING person_id"
        )
        person_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO role_assignment (governance_role_id, person_id) VALUES (%s, %s) RETURNING role_assignment_id",
            (role_id, person_id),
        )
        ra_id = cur.fetchone()[0]

        cur.execute(
            "SELECT role_name, full_name, organization FROM vw_governance_assignments WHERE role_assignment_id = %s",
            (ra_id,),
        )
        row = cur.fetchone()
        assert row == ("Auditor", "Jane Doe", "DGT")


def test_data_access_request_joins_decision_log(db_txn):
    with db_txn.cursor() as cur:
        cur.execute(
            "INSERT INTO dataset (title, source_identifier) VALUES ('Access DS', 'access-1') RETURNING dataset_id"
        )
        ds_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO decision_log (dataset_id, decision_type, decision_text, decided_by)
               VALUES (%s, 'access', 'Approved for research', 'Admin') RETURNING decision_log_id""",
            (ds_id,),
        )
        dl_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO data_access_request (dataset_id, requested_by, purpose, status, decision_log_id)
               VALUES (%s, 'researcher@example.com', 'Research', 'approved', %s) RETURNING request_id""",
            (ds_id, dl_id),
        )
        req_id = cur.fetchone()[0]

        cur.execute(
            "SELECT decision_type, decided_by FROM vw_data_access_request WHERE request_id = %s",
            (req_id,),
        )
        row = cur.fetchone()
        assert row == ("access", "Admin")

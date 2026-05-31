_EXPECTED_ROLES = {
    "Data Owner",
    "Data Steward",
    "Privacy Officer",
    "Security Officer",
    "Data Governance Council Chair",
}

_EXPECTED_POLICIES = {
    "Privacy Act of 1974",
    "CIPSEA Confidentiality",
    "OMB M-19-23 FDS Strategy",
    "FedRAMP High Baseline",
    "Records Retention Schedule",
}

_EXPECTED_POLICY_TYPES = {"privacy", "governance", "cybersecurity", "retention"}

_EXPECTED_SECURITY_MARKINGS = {
    "Public",
    "Controlled Unclassified Information",
    "High-Value Asset",
}

_EXPECTED_CLASSIFICATION_LEVELS = {"low", "moderate", "high"}


def _scalar(conn, sql, *args):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()[0]


def _column(conn, sql, *args):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return {row[0] for row in cur.fetchall()}


def test_governance_role_count(db):
    assert _scalar(db, "SELECT COUNT(*) FROM governance_role") == 5


def test_governance_role_names(db):
    names = _column(db, "SELECT name FROM governance_role")
    assert names == _EXPECTED_ROLES


def test_governance_role_authority_levels_set(db):
    levels = _column(db, "SELECT DISTINCT authority_level FROM governance_role")
    assert "executive" in levels
    assert "manager" in levels


def test_policy_count(db):
    assert _scalar(db, "SELECT COUNT(*) FROM policy") == 5


def test_policy_names(db):
    names = _column(db, "SELECT name FROM policy")
    assert names == _EXPECTED_POLICIES


def test_policy_types_coverage(db):
    types = _column(db, "SELECT DISTINCT policy_type FROM policy")
    assert types == _EXPECTED_POLICY_TYPES


def test_security_marking_count(db):
    assert _scalar(db, "SELECT COUNT(*) FROM security_marking") == 3


def test_security_marking_names(db):
    names = _column(db, "SELECT name FROM security_marking")
    assert names == _EXPECTED_SECURITY_MARKINGS


def test_security_marking_classification_levels(db):
    levels = _column(db, "SELECT DISTINCT classification_level FROM security_marking")
    assert levels == _EXPECTED_CLASSIFICATION_LEVELS


def test_permissible_use_count(db):
    assert _scalar(db, "SELECT COUNT(*) FROM permissible_use") == 5


def test_permissible_use_linked_to_policies(db):
    orphaned = _scalar(
        db,
        "SELECT COUNT(*) FROM permissible_use pu LEFT JOIN policy p ON p.policy_id = pu.policy_id WHERE p.policy_id IS NULL",
    )
    assert orphaned == 0


def test_privacy_act_requires_approval(db):
    count = _scalar(
        db,
        """
        SELECT COUNT(*) FROM permissible_use pu
        JOIN policy p ON p.policy_id = pu.policy_id
        WHERE p.name = 'Privacy Act of 1974' AND pu.requires_approval = true
        """,
    )
    assert count > 0

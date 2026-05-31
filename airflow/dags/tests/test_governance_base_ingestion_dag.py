from datetime import timedelta

import pytest

DAG_ID = "governance_base_table_ingestion"

_EXPECTED_TASKS = {
    "ingest_base_tables",
    "profile_base_tables",
}


@pytest.fixture(scope="module")
def dag(dagbag):
    return dagbag.get_dag(DAG_ID)


def test_dag_loaded(dagbag):
    assert dagbag.get_dag(DAG_ID) is not None


def test_dag_id(dag):
    assert dag.dag_id == DAG_ID


def test_catchup_disabled(dag):
    assert dag.catchup is False


def test_schedule(dag):
    assert str(dag.schedule) == "0 5 * * *"


def test_task_count(dag):
    assert len(dag.tasks) == 2


def test_task_ids(dag):
    assert {t.task_id for t in dag.tasks} == _EXPECTED_TASKS


def test_dependency_chain(dag):
    ingest = dag.get_task("ingest_base_tables")
    profile = dag.get_task("profile_base_tables")

    assert "profile_base_tables" in ingest.downstream_task_ids
    assert not profile.downstream_task_ids


def test_retries(dag):
    assert dag.get_task("ingest_base_tables").retries == 1


def test_retry_delay(dag):
    assert dag.get_task("ingest_base_tables").retry_delay == timedelta(minutes=10)


def test_owner(dag):
    assert dag.get_task("ingest_base_tables").owner == "governance-team"


def test_tags(dag):
    assert "openmetadata" in dag.tags
    assert "governance" in dag.tags
    assert "tables" in dag.tags

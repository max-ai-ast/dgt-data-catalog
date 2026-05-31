from datetime import timedelta

import pytest

DAG_ID = "clue_metadata_ingestion"

_EXPECTED_TASKS = {
    "ingest_openmetadata_views",
    "profile_openmetadata_views",
    "ingest_openmetadata_lineage",
    "ingest_openmetadata_classification",
}


@pytest.fixture(scope="module")
def dag(dagbag):
    return dagbag.get_dag(DAG_ID)


def test_dag_loaded(dagbag):
    assert not dagbag.import_errors
    assert dagbag.get_dag(DAG_ID) is not None


def test_dag_id(dag):
    assert dag.dag_id == DAG_ID


def test_catchup_disabled(dag):
    assert dag.catchup is False


def test_schedule(dag):
    assert str(dag.schedule_interval) == "0 6 * * *"


def test_task_count(dag):
    assert len(dag.tasks) == 4


def test_task_ids(dag):
    assert {t.task_id for t in dag.tasks} == _EXPECTED_TASKS


def test_dependency_chain(dag):
    ingest = dag.get_task("ingest_openmetadata_views")
    profile = dag.get_task("profile_openmetadata_views")
    lineage = dag.get_task("ingest_openmetadata_lineage")
    classify = dag.get_task("ingest_openmetadata_classification")

    assert "profile_openmetadata_views" in ingest.downstream_task_ids
    assert "ingest_openmetadata_lineage" in profile.downstream_task_ids
    assert "ingest_openmetadata_classification" in lineage.downstream_task_ids
    assert not classify.downstream_task_ids


def test_retries(dag):
    task = dag.get_task("ingest_openmetadata_views")
    assert task.retries == 1


def test_retry_delay(dag):
    task = dag.get_task("ingest_openmetadata_views")
    assert task.retry_delay == timedelta(minutes=5)


def test_owner(dag):
    task = dag.get_task("ingest_openmetadata_views")
    assert task.owner == "governance-team"


def test_tags(dag):
    assert "openmetadata" in dag.tags
    assert "governance" in dag.tags

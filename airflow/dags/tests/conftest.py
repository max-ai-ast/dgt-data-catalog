import os

import pytest

os.environ.setdefault("AIRFLOW__CORE__UNIT_TEST_MODE", "True")

from airflow.models import DagBag  # noqa: E402

_DAG_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def dagbag():
    return DagBag(dag_folder=_DAG_DIR, include_examples=False)

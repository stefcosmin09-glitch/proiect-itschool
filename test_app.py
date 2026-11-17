import pytest

import app as app_module
from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    app_module.TASKS.clear()
    app_module.seed()
    with app.test_client() as test_client:
        yield test_client


def test_home_page_lists_seeded_tasks(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Buy groceries" in response.data


def test_add_task_persists_in_store(client):
    response = client.post("/add", data={"task": "  Ship the pipeline  "})
    assert response.status_code == 302
    assert "Ship the pipeline" in app_module.TASKS.values()


def test_add_task_ignores_blank_input(client):
    before = len(app_module.TASKS)
    client.post("/add", data={"task": "   "})
    assert len(app_module.TASKS) == before


def test_delete_removes_only_that_task(client):
    task_id = next(iter(app_module.TASKS))
    victim = app_module.TASKS[task_id]
    client.get(f"/delete/{task_id}")
    assert victim not in app_module.TASKS.values()


def test_delete_unknown_id_returns_404_not_500(client):
    # Regression: pop(index) pe o lista arunca IndexError -> HTTP 500.
    assert client.get("/delete/does-not-exist").status_code == 404


def test_delete_stale_link_does_not_remove_other_task(client):
    # Regression: index-urile se deplaseaza la stergere, deci un link vechi
    # stingea alt task. Cheile stabile elimina clasa de bug.
    first = next(iter(app_module.TASKS))
    client.get(f"/delete/{first}")
    assert len(app_module.TASKS) == 2


def test_task_text_is_escaped(client):
    client.post("/add", data={"task": "<script>alert(1)</script>"})
    response = client.get("/")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_api_tasks_returns_json(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.json is not None
    assert len(response.json["tasks"]) == 3


def test_healthz_and_readyz(client):
    assert client.get("/healthz").status_code == 200
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json["tasks"] == 3


def test_metrics_exposes_prometheus_series(client):
    client.get("/")
    body = client.get("/metrics").data.decode()
    assert "todo_http_requests_total" in body
    assert "todo_tasks_in_memory" in body


def test_about_page(client):
    assert client.get("/about").status_code == 200


def test_add_task_rejects_too_long_input(client):
    # Un text peste limita nu trebuie sa ocupe memoria procesului.
    before = len(app_module.TASKS)
    client.post("/add", data={"task": "x" * (app_module.MAX_TASK_LENGTH + 1)})
    assert len(app_module.TASKS) == before

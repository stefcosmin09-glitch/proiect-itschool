import os
import time
import uuid

from flask import Flask, Response, abort, g, jsonify, redirect, request
from markupsafe import escape
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)

# Cand gunicorn ruleaza cu mai multi workeri, fiecare proces are propriul
# registry in memorie. Modul multiproct se salveaza pe disc si se combina la
# scrape, ca sa nu se piarda metricile.
MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

REGISTRY = CollectorRegistry()
if MULTIPROC_DIR:
    multiprocess.MultiProcessCollector(REGISTRY)

REQUESTS = Counter(
    "todo_http_requests_total",
    "Total de cereri HTTP",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)
LATENCY = Histogram(
    "todo_http_request_duration_seconds",
    "Latenta cererilor HTTP",
    ["method", "endpoint"],
    registry=REGISTRY,
)
TASKS_IN_MEMORY = Gauge(
    "todo_tasks_in_memory",
    "Numar de task-uri pastrate in memoria procesului",
    registry=REGISTRY,
)

app = Flask(__name__)

# Limita de lungime pentru un task: fara ea, un singur request cu un text urias
# ar putea umple memoria procesului (DoS accidental sau intentionat).
MAX_TASK_LENGTH = 200

# LIMITARE CUNOSCUTA: starea este in memoria procesului, deci nu este partajata
# intre replici. Cu replicas > 1 un task adaugat pe o replica nu apare pe
# cealalta, iar un restart pierde tot. Rezolvarea (Postgres + Alembic) este
# urmatorul pas, vezi README -> Roadmap.
TASKS: dict[str, str] = {}


def seed() -> None:
    for text in ("Buy groceries", "Clean the house", "Pay bills"):
        TASKS[uuid.uuid4().hex] = text
    TASKS_IN_MEMORY.set(len(TASKS))


seed()


@app.before_request
def start_timer():
    g.started_at = time.monotonic()


@app.after_request
def observe(response):
    endpoint = request.endpoint or "unknown"
    REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
    started_at = getattr(g, "started_at", None)
    if started_at is not None:
        LATENCY.labels(request.method, endpoint).observe(time.monotonic() - started_at)
    return response


@app.get("/")
def index():
    items = "".join(
        f'<li>{escape(text)} <a href="/delete/{task_id}" aria-label="delete">X</a></li>'
        for task_id, text in TASKS.items()
    )
    return f"""
        <h1>To do List</h1>
        <ul>{items}</ul>
        <form method="POST" action="/add">
            <input type="text" name="task" placeholder="New task" required>
            <button type="submit">Add Task</button>
        </form>
    """


@app.post("/add")
def add_task():
    task = (request.form.get("task") or "").strip()
    # Fara limita, un request cu un text urias ar umple memoria procesului.
    if task and len(task) <= MAX_TASK_LENGTH:
        TASKS[uuid.uuid4().hex] = task
        TASKS_IN_MEMORY.set(len(TASKS))
    return redirect("/")


@app.get("/delete/<task_id>")
def delete_task(task_id: str):
    # Inainte era pop(index) pe o lista: index out of range -> 500, iar stergerea
    # unui task muta toti indicii urmatori, deci link-urile vechi stingeau alt
    # task. Chei stabile + 404 in loc de 500.
    if TASKS.pop(task_id, None) is None:
        abort(404)
    TASKS_IN_MEMORY.set(len(TASKS))
    return redirect("/")


@app.get("/api/tasks")
def api_tasks():
    return jsonify(tasks=[{"id": task_id, "text": text} for task_id, text in TASKS.items()])


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.get("/readyz")
def readyz():
    return jsonify(status="ready", tasks=len(TASKS))


@app.get("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)


@app.get("/about")
def about():
    return "<h1>About Us</h1>"


if __name__ == "__main__":
    # Doar pentru dezvoltare locala. In containere ruleaza gunicorn (vezi Dockerfile).
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )

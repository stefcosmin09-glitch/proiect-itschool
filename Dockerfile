# syntax=docker/dockerfile:1
#
# Multi-stage, pe randuri:
#   builder -> venv cu dependintele de productie
#   test    -> builder + dependinte de test, ruleaza pytest (target pentru CI)
#   runtime -> imaginea finala: non-root, doar venv-ul, gunicorn
#
# Build:  docker build -t todo-app .
# Test:   docker build --target test -t todo-app:test . && docker run --rm todo-app:test

ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------- base
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---------------------------------------------------------------- builder
FROM base AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv "$VIRTUAL_ENV"

COPY requirements.txt ./
RUN pip install -r requirements.txt

# ---------------------------------------------------------------- test
FROM builder AS test

WORKDIR /src

COPY requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY app.py test_app.py ./

CMD ["python", "-m", "pytest", "-q"]

# ---------------------------------------------------------------- runtime
FROM base AS runtime

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PORT=5000 \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# Utilizator ne-privilegiat, UID/GID fix ca sa poata fi legat ca volum de K8s
RUN groupadd --system --gid 1001 app \
 && useradd --system --uid 1001 --gid 1001 --shell /usr/sbin/nologin app \
 && mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

COPY --from=builder --chown=1001:1001 /opt/venv /opt/venv

WORKDIR /app
COPY --chown=1001:1001 app.py ./

USER 1001:1001

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=2).status == 200 else 1)"]

# Server WSGI de productie. Bare-ul Flask development server nu se foloseste niciodata in produs.
ENTRYPOINT ["gunicorn"]
CMD ["--bind=0.0.0.0:5000", \
     "--workers=2", \
     "--threads=4", \
     "--timeout=30", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "app:app"]

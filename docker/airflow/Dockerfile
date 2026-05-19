# Production Airflow image — Python deps and src/ only; DAGs are synced via git-sync.
# syntax=docker/dockerfile:1

FROM apache/airflow:3.0.2-python3.12

LABEL org.opencontainers.image.title="etf-forecast-airflow" \
    org.opencontainers.image.description="Airflow 3 runtime with project dependencies and src (DAGs via git-sync)"

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/

USER airflow

ENV UV_CACHE_DIR=/tmp/uv-cache \
    PYTHONPATH=/opt/airflow:/opt/airflow/dags \
    AIRFLOW_HOME=/opt/airflow \
    AIRFLOW__CORE__LOAD_EXAMPLES=false \
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true

WORKDIR /opt/airflow

COPY --chown=airflow:root pyproject.toml uv.lock ./

RUN uv pip install -r pyproject.toml --extra airflow

COPY --chown=airflow:root src/ ./src/

RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins \
    && airflow version

WORKDIR /opt/airflow

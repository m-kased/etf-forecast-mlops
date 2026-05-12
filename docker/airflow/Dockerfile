FROM apache/airflow:3.0.2-python3.12

USER root

# Install uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER airflow

# Copy pyproject.toml into the image
COPY --chown=airflow:root pyproject.toml /opt/airflow/pyproject.toml
COPY --chown=airflow:root uv.lock /opt/airflow/uv.lock

#Install dependencies
RUN uv pip install -r /opt/airflow/pyproject.toml

# 3. Copy DAGs and supporting modules
COPY --chown=airflow:root dags/ /opt/airflow/dags/
COPY --chown=airflow:root src/ /opt/airflow/src/

# Set Python path to include src
ENV PYTHONPATH="/opt/airflow:/opt/airflow/dags"

# Create directories for logs and plugins
RUN mkdir -p /opt/airflow/logs /opt/airflow/plugins

# Set working directory
WORKDIR /opt/airflow

from datetime import datetime, timedelta
import os

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.data.etl import run_pipeline
from src.ml.train import run_training_pipeline

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

default_args = {
    "owner": "mlops_engineer",
    "depends_on_past": False,
    "start_date": datetime(2026, 5, 10),
    "email_on_failure": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def reload_api_models(**context):
    """Reload API models only if training promoted a new champion."""
    ti = context["ti"]
    new_champion = ti.xcom_pull(task_ids="train_models")
    if not new_champion:
        ti.log.info("No new champion promoted — skipping API reload.")
        return
    resp = requests.post(f"{API_BASE_URL}/reload", timeout=60)
    resp.raise_for_status()
    ti.log.info("API reload response: %s", resp.json())


with DAG(
    dag_id="etf_hourly_feature_pipeline",
    default_args=default_args,
    description="Fetches ETF data, calculates technical indicators, and saves to MinIO.",
    schedule="@hourly",
    catchup=False,
    tags=["finance", "etl"],
) as dag:
    run_etl_task = PythonOperator(
        task_id="extract_transform_load_to_minio",
        python_callable=run_pipeline,
    )

    run_training_task = PythonOperator(
        task_id="train_models",
        python_callable=run_training_pipeline,
    )

    reload_task = PythonOperator(
        task_id="reload_api_models",
        python_callable=reload_api_models,
    )

    run_etl_task >> run_training_task >> reload_task

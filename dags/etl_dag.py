from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.data.etl import run_pipeline
from src.ml.train import run_training_pipeline

default_args = {
    'owner': 'mlops_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 10), # Start date in the past so it activates immediately
    'email_on_failure': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    dag_id='etf_hourly_feature_pipeline',
    default_args=default_args,
    description='Fetches ETF data, calculates technical indicators, and saves to MinIO.',
    schedule='@hourly',
    catchup=False,
    tags=['finance', 'etl'],
) as dag:

    # Define the Task
    run_etl_task = PythonOperator(
        task_id='extract_transform_load_to_minio',
        python_callable=run_pipeline,
    )

    # Define the Task
    run_training_task = PythonOperator(
        task_id='train_models',
        python_callable=run_training_pipeline,
    )

    # Set the Task Dependencies
    run_etl_task >> run_training_task
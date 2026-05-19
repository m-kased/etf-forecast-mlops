"""Prometheus metrics shared by API, ETL, and training workloads."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager

from prometheus_client import Counter, Gauge, Histogram, REGISTRY, push_to_gateway

logger = logging.getLogger(__name__)

PUSHGATEWAY_URL = (os.getenv("PROMETHEUS_PUSHGATEWAY_URL") or "").strip().rstrip("/")

# --- API (scraped from /metrics on the FastAPI pod) ---

PREDICTIONS_TOTAL = Counter(
    "etf_forecast_predictions_total",
    "Prediction requests",
    ["ticker", "status"],
)

PREDICTION_VOLATILITY = Histogram(
    "etf_forecast_prediction_volatility",
    "Predicted volatility values",
    ["ticker"],
    buckets=(0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.2),
)

MODEL_RELOADS_TOTAL = Counter(
    "etf_forecast_model_reloads_total",
    "Model cache reload operations",
    ["scope", "status"],
)

MODELS_LOADED = Gauge(
    "etf_forecast_models_loaded",
    "Number of models currently loaded in API memory",
)

# --- ETL (pushed to Pushgateway after each Airflow/local run) ---

ETL_RUNS_TOTAL = Counter(
    "etf_forecast_etl_runs_total",
    "ETL pipeline executions",
    ["status"],
)

ETL_TICKERS_PROCESSED = Counter(
    "etf_forecast_etl_tickers_processed_total",
    "Tickers successfully processed in ETL",
    ["ticker"],
)

ETL_ROWS_TOTAL = Counter(
    "etf_forecast_etl_rows_total",
    "Feature rows written per ticker",
    ["ticker"],
)

ETL_DURATION_SECONDS = Histogram(
    "etf_forecast_etl_duration_seconds",
    "End-to-end ETL pipeline duration",
    buckets=(5, 15, 30, 60, 120, 300, 600),
)

ETL_LAST_TICKER_COUNT = Gauge(
    "etf_forecast_etl_last_ticker_count",
    "Tickers processed in the most recent ETL run",
)

# --- Training (pushed to Pushgateway after each run) ---

TRAINING_RUNS_TOTAL = Counter(
    "etf_forecast_training_runs_total",
    "Per-ticker training runs",
    ["ticker", "status"],
)

TRAINING_RMSE = Gauge(
    "etf_forecast_training_rmse",
    "RMSE from the latest training run per ticker",
    ["ticker"],
)

CHAMPION_PROMOTIONS_TOTAL = Counter(
    "etf_forecast_champion_promotions_total",
    "Times a new champion model was promoted",
    ["ticker"],
)

TRAINING_DURATION_SECONDS = Histogram(
    "etf_forecast_training_duration_seconds",
    "Per-ticker training duration",
    ["ticker"],
    buckets=(5, 15, 30, 60, 120, 300, 600),
)


@contextmanager
def observe_duration(histogram: Histogram, **labels: str):
    """Record elapsed wall time into a (optionally labeled) histogram."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        if labels:
            histogram.labels(**labels).observe(elapsed)
        else:
            histogram.observe(elapsed)


def push_metrics(job: str, grouping_key: dict[str, str] | None = None) -> None:
    """Push default-registry metrics to Prometheus Pushgateway (batch jobs)."""
    if not PUSHGATEWAY_URL:
        logger.debug("PROMETHEUS_PUSHGATEWAY_URL unset; skipping metrics push")
        return
    try:
        push_to_gateway(
            PUSHGATEWAY_URL,
            job=job,
            registry=REGISTRY,
            grouping_key=grouping_key or {},
        )
        logger.info("Pushed metrics to Pushgateway job=%s", job)
    except Exception as exc:
        logger.warning("Failed to push metrics to Pushgateway: %s", exc)


def airflow_grouping_key() -> dict[str, str]:
    """Labels that isolate concurrent Airflow task instances on Pushgateway."""
    return {
        k: v
        for k, v in {
            "dag_id": os.getenv("AIRFLOW_CTX_DAG_ID"),
            "task_id": os.getenv("AIRFLOW_CTX_TASK_ID"),
            "run_id": os.getenv("AIRFLOW_CTX_DAG_RUN_ID"),
        }.items()
        if v
    }

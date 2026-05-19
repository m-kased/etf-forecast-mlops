import logging
import math
import os
import sys

import boto3
import mlflow
import mlflow.xgboost
import pandas as pd
import xgboost as xgb
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from mlflow import MlflowClient
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from common.db import get_active_tickers

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MLFLOW_TRACKING_URI = "http://localhost:5000"
MLFLOW_EXPERIMENT = "ETF_Volatility_Prediction"

MLFLOW_URI = (os.getenv("MLFLOW_TRACKING_URI") or DEFAULT_MLFLOW_TRACKING_URI).strip()
MLFLOW_ARTIFACT_BUCKET = (
    os.getenv("MLFLOW_S3_ARTIFACT_BUCKET") or "mlflow-artifacts"
).strip()
DATA_LAKE_BUCKET = (
    os.getenv("S3_DATA_BUCKET") or os.getenv("RAW_DATA_BUCKET") or "market-features"
).strip()

_s3_client = None
_mlflow_configured = False


def require_env_vars(names: tuple[str, ...]) -> None:
    missing = [n for n in names if not (os.getenv(n) or "").strip()]
    if missing:
        logger.error(
            "Missing or empty required environment variables: %s",
            ", ".join(missing),
        )
        sys.exit(1)


def _s3_client_kwargs() -> dict:
    """MinIO when an endpoint is set; otherwise AWS S3 via IRSA/default credential chain."""
    kwargs: dict = {}
    region = (os.getenv("AWS_DEFAULT_REGION") or "").strip()
    if region:
        kwargs["region_name"] = region
    endpoint = (
        os.getenv("MINIO_ENDPOINT") or os.getenv("MLFLOW_S3_ENDPOINT_URL") or ""
    ).strip()
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    access = (
        os.getenv("MINIO_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID") or ""
    ).strip()
    secret = (
        os.getenv("MINIO_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY") or ""
    ).strip()
    if access and secret:
        kwargs["aws_access_key_id"] = access
        kwargs["aws_secret_access_key"] = secret
    elif endpoint:
        require_env_vars(("MINIO_ACCESS_KEY", "MINIO_SECRET_KEY"))
        kwargs["aws_access_key_id"] = os.environ["MINIO_ACCESS_KEY"].strip()
        kwargs["aws_secret_access_key"] = os.environ["MINIO_SECRET_KEY"].strip()
    return kwargs


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", **_s3_client_kwargs())
    return _s3_client


def configure_mlflow() -> None:
    global _mlflow_configured
    if _mlflow_configured:
        return
    logger.info("Connecting to MLflow at %s", MLFLOW_URI)
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    _mlflow_configured = True
    logger.info("MLflow tracking URI configured")


def ensure_bucket_exists(bucket_name: str) -> None:
    """Create the MinIO bucket if missing (same pattern as ETL for market-features)."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3.create_bucket(Bucket=bucket_name)


def train_model(ticker: str = "SPY") -> bool:
    ensure_bucket_exists(MLFLOW_ARTIFACT_BUCKET)
    ensure_bucket_exists(DATA_LAKE_BUCKET)
    logger.info("Starting training pipeline for %s", ticker)

    local_path = f"/tmp/{ticker}_features.parquet"
    logger.info("Downloading %s features from %s", ticker, DATA_LAKE_BUCKET)
    get_s3_client().download_file(
        DATA_LAKE_BUCKET, f"{ticker}_features.parquet", local_path
    )

    df = pd.read_parquet(local_path)
    features = ["log_return", "RSI_14", "MACD_12_26_9"]
    df = df.dropna(subset=features + ["target_volatility_6h"])

    X = df[features]
    y = df["target_volatility_6h"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    with mlflow.start_run(run_name=f"{ticker}_XGBoost_Baseline"):
        logger.info("Training XGBoost model for %s", ticker)

        params = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 5,
            "random_state": 42,
        }
        mlflow.log_params(params)
        mlflow.log_param("ticker", ticker)

        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        rmse = math.sqrt(mean_squared_error(y_test, predictions))
        logger.info("Model RMSE for %s: %.5f", ticker, rmse)

        mlflow.log_metric("rmse", rmse)
        mlflow.xgboost.log_model(model, name="xgboost_model")

        client = MlflowClient()
        registry_name = f"etf-vol-{ticker}"
        run_id = mlflow.active_run().info.run_id
        model_uri = f"runs:/{run_id}/xgboost_model"
        mv = mlflow.register_model(model_uri, registry_name)

        promoted = False
        try:
            champion_mv = client.get_model_version_by_alias(registry_name, "champion")
            champion_run = client.get_run(champion_mv.run_id)
            champion_rmse = champion_run.data.metrics["rmse"]
            if rmse < champion_rmse:
                client.set_registered_model_alias(registry_name, "champion", mv.version)
                logger.info(
                    "New champion for %s: v%s (RMSE %.5f < %.5f)",
                    ticker,
                    mv.version,
                    rmse,
                    champion_rmse,
                )
                promoted = True
            else:
                logger.info(
                    "Existing champion retained for %s (RMSE %.5f <= %.5f)",
                    ticker,
                    champion_rmse,
                    rmse,
                )
        except Exception:
            client.set_registered_model_alias(registry_name, "champion", mv.version)
            logger.info(
                "First model for %s promoted to champion (v%s)",
                ticker,
                mv.version,
            )
            promoted = True

        return promoted


def run_training_pipeline() -> bool:
    """Train models for all active ETFs. Returns True if any champion was promoted."""
    configure_mlflow()
    tickers = get_active_tickers()
    logger.info("Training pipeline starting for tickers: %s", tickers)
    any_promoted = False
    for ticker in tickers:
        if train_model(ticker):
            any_promoted = True
    logger.info("Training pipeline completed (new_champion=%s)", any_promoted)
    return any_promoted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    configure_mlflow()
    train_model("SPY")

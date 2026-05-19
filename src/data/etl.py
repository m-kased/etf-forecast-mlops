import logging
import os
from pathlib import Path

import boto3
import numpy as np
import pandas as pd
import pandas_ta  # noqa: F401 — registers .ta accessors on DataFrame
import yfinance as yf
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from common.db import get_active_tickers
from common.metrics import (
    ETL_DURATION_SECONDS,
    ETL_LAST_TICKER_COUNT,
    ETL_ROWS_TOTAL,
    ETL_RUNS_TOTAL,
    ETL_TICKERS_PROCESSED,
    airflow_grouping_key,
    observe_duration,
    push_metrics,
)

HORIZON_BARS = 6
DATA_DIR = Path("/tmp/market_data")
DATA_BUCKET = (
    os.getenv("S3_DATA_BUCKET") or os.getenv("RAW_DATA_BUCKET") or "market-features"
).strip()

load_dotenv()

_s3_client = None
_s3_presign_client = None
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _s3_client_kwargs() -> dict:
    """Build boto3 S3 kwargs for MinIO (local) or AWS S3 with IRSA (EKS)."""
    kwargs: dict = {}
    region = (os.getenv("AWS_DEFAULT_REGION") or "").strip()
    if region:
        kwargs["region_name"] = region
    endpoint = _normalize_minio_endpoint(os.getenv("MINIO_ENDPOINT"))
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
    return kwargs


def get_s3_client():
    """S3 client for uploads (MinIO locally, AWS S3 + IRSA on EKS)."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", **_s3_client_kwargs())
    return _s3_client


def get_s3_presign_client():
    """Client used only to sign GET URLs. Use MINIO_PUBLIC_URL so links work outside Docker."""
    global _s3_presign_client
    if _s3_presign_client is None:
        kwargs = _s3_client_kwargs()
        public = os.getenv("MINIO_PUBLIC_URL") or os.getenv("MINIO_ENDPOINT")
        if public:
            kwargs["endpoint_url"] = _normalize_minio_endpoint(public)
        _s3_presign_client = boto3.client("s3", **kwargs)
    return _s3_presign_client


def _normalize_minio_endpoint(raw: str | None) -> str:
    """Botocore requires a full URL; bare host:port from env raises Invalid endpoint."""
    endpoint = (raw or "http://minio:9000").strip()
    if not endpoint.startswith(("http://", "https://")):
        endpoint = f"http://{endpoint}"
    return endpoint.rstrip("/")


def ensure_bucket_exists(bucket_name: str) -> None:
    """Create the MinIO bucket if it does not exist yet."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        logger.info("Bucket %r not found; creating it", bucket_name)
        s3.create_bucket(Bucket=bucket_name)


def extract_data(ticker: str, period="1y", interval="1h") -> pd.DataFrame:
    """Extract raw OHLCV data from yfinance."""
    logger.info("Downloading raw data for %s", ticker)
    df = yf.download(ticker, period=period, interval=interval, progress=False)

    if df.empty:
        logger.error("Failed to fetch data for %s", ticker)
        return pd.DataFrame()

    df.columns = (
        df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
    )
    df.columns = [c.lower() for c in df.columns]
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply technical indicators and generate the volatility target label."""
    logger.info("Applying technical indicators and generating labels")

    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df["target_volatility_6h"] = (
        df["log_return"].shift(-HORIZON_BARS).rolling(window=HORIZON_BARS).std()
    )
    return df.dropna().copy()


def load_data(df: pd.DataFrame, ticker: str) -> str:
    """Save locally, upload to object storage, return a presigned GET URL."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{ticker}_features.parquet"
    local_path = DATA_DIR / file_name

    df.to_parquet(local_path)
    logger.info("Saved %s rows locally to %s", len(df), local_path)

    logger.info("Uploading %s to bucket %r", file_name, DATA_BUCKET)
    get_s3_client().upload_file(str(local_path), DATA_BUCKET, file_name)
    logger.info("Upload successful")

    expires = int(os.getenv("MINIO_PRESIGNED_EXPIRES", "86400"))
    download_url = get_s3_presign_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": DATA_BUCKET, "Key": file_name},
        ExpiresIn=expires,
    )
    logger.info("Presigned download URL (expires in %ss)", expires)
    return download_url


def run_pipeline() -> dict[str, str]:
    """Run ETL for all tickers. Returns ticker -> presigned URL for Airflow XCom."""
    with observe_duration(ETL_DURATION_SECONDS):
        tickers = get_active_tickers()
        logger.info("Starting ETL pipeline for tickers: %s", tickers)
        ensure_bucket_exists(DATA_BUCKET)

        uploaded: dict[str, str] = {}
        try:
            for ticker in tickers:
                df = extract_data(ticker)
                if df.empty:
                    continue
                clean_df = transform_data(df)
                uploaded[ticker] = load_data(clean_df, ticker)
                ETL_TICKERS_PROCESSED.labels(ticker=ticker).inc()
                ETL_ROWS_TOTAL.labels(ticker=ticker).inc(len(clean_df))

            ETL_LAST_TICKER_COUNT.set(len(uploaded))
            ETL_RUNS_TOTAL.labels(status="success").inc()
            logger.info(
                "ETL pipeline complete — data under %s, bucket %r, URLs: %s",
                DATA_DIR,
                DATA_BUCKET,
                uploaded,
            )
            return uploaded
        except Exception:
            ETL_RUNS_TOTAL.labels(status="error").inc()
            raise
        finally:
            push_metrics("etf-etl", grouping_key=airflow_grouping_key())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Pipeline result: %s", run_pipeline())

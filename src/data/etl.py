import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import os

from dotenv import load_dotenv
from common.db import get_active_tickers

HORIZON_BARS = 6
DATA_DIR = Path("/tmp/market_data")
MINIO_BUCKET = "market-features"

load_dotenv()

_s3_client = None
_s3_presign_client = None
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_s3_client():
    """S3 client for uploads (uses MINIO_ENDPOINT — reachable from this process)."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=_normalize_minio_endpoint(os.getenv("MINIO_ENDPOINT")),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        )
    return _s3_client


def get_s3_presign_client():
    """Client used only to sign GET URLs. Use MINIO_PUBLIC_URL so links work outside Docker."""
    global _s3_presign_client
    if _s3_presign_client is None:
        public = os.getenv("MINIO_PUBLIC_URL") or os.getenv("MINIO_ENDPOINT")
        _s3_presign_client = boto3.client(
            "s3",
            endpoint_url=_normalize_minio_endpoint(public),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        )
    return _s3_presign_client

def _normalize_minio_endpoint(raw: str | None) -> str:
    """Botocore requires a full URL; bare host:port from env raises Invalid endpoint."""
    endpoint = (raw or "http://minio:9000").strip()
    if not endpoint.startswith(("http://", "https://")):
        endpoint = f"http://{endpoint}"
    return endpoint.rstrip("/")

def ensure_bucket_exists(bucket_name: str):
    """Creates the MinIO bucket if it doesn't exist yet."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        logger.info(f"Bucket '{bucket_name}' not found. Creating it...")
        s3.create_bucket(Bucket=bucket_name)

def extract_data(ticker: str, period="1y", interval="1h") -> pd.DataFrame:
    """Extracts raw OHLCV data from yfinance"""
    logger.info(f"Downloading raw data for {ticker}...")
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if df.empty:
        logger.error(f"Failed to fetch data for {ticker}")
        return pd.DataFrame()
        
    # clean up column names
    df.columns = df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
    # make columns lowercase
    df.columns = [c.lower() for c in df.columns]
    return df

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applies financial math to generate features and target labels"""
    logger.info("Applying technical indicators and generating labels...")
    
    # Base log returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # Features via pandas_ta
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    
    # Target Label (Future Volatility)
    df['target_volatility_6h'] = df['log_return'].shift(-HORIZON_BARS).rolling(window=HORIZON_BARS).std()
    
    # drop rows with NaN values
    clean_df = df.dropna().copy()
    return clean_df

def load_data(df: pd.DataFrame, ticker: str) -> str:
    """Save locally, upload to MinIO, return a time-limited presigned GET URL."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{ticker}_features.parquet"
    local_path = DATA_DIR / file_name

    # Save Locally
    df.to_parquet(local_path)
    logger.info(f"Saved {len(df)} rows locally to {local_path}")

    # Upload to MinIO
    logger.info(f"Uploading {file_name} to MinIO bucket '{MINIO_BUCKET}'...")
    get_s3_client().upload_file(str(local_path), MINIO_BUCKET, file_name)
    logger.info("Upload successful")

    expires = int(os.getenv("MINIO_PRESIGNED_EXPIRES", "86400"))
    download_url = get_s3_presign_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": MINIO_BUCKET, "Key": file_name},
        ExpiresIn=expires,
    )
    logger.info("Presigned download URL (expires in %ss)", expires)
    return download_url

def run_pipeline() -> dict[str, str]:
    """Run ETL for all tickers. Returns ticker -> object URL for Airflow XCom."""
    tickers = get_active_tickers()
    logger.info("Starting ETL Pipeline for tickers: %s", tickers)
    ensure_bucket_exists(MINIO_BUCKET)

    uploaded: dict[str, str] = {}
    for ticker in tickers:
        df = extract_data(ticker)
        if df.empty:
            continue
        clean_df = transform_data(df)
        uploaded[ticker] = load_data(clean_df, ticker)

    logger.info("ETL Pipeline Complete")
    logger.info(
        "Data under %s; MinIO bucket %r; URLs: %s",
        DATA_DIR,
        MINIO_BUCKET,
        uploaded,
    )
    return uploaded


if __name__ == "__main__":
    print(run_pipeline())
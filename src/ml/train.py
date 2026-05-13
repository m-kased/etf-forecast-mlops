import os
import sys
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import math
import mlflow
import mlflow.xgboost
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Setup Environment variables
load_dotenv()

DEFAULT_MINIO_ENDPOINT = "http://localhost:9000"
DEFAULT_MLFLOW_TRACKING_URI = "http://localhost:5000"

REQUIRED_ENV = (
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "MLFLOW_S3_ENDPOINT_URL",
)

def require_env_vars(names: tuple[str, ...]) -> None:
    missing = [n for n in names if not (os.getenv(n) or "").strip()]
    if missing:
        print(
            "Missing or empty required environment variables: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        sys.exit(1)


require_env_vars(REQUIRED_ENV)

MINIO_ENDPOINT = (os.getenv("MINIO_ENDPOINT") or DEFAULT_MINIO_ENDPOINT).strip()
MINIO_ACCESS = os.environ["MINIO_ACCESS_KEY"].strip()
MINIO_SECRET = os.environ["MINIO_SECRET_KEY"].strip()
MLFLOW_URI = (os.getenv("MLFLOW_TRACKING_URI") or DEFAULT_MLFLOW_TRACKING_URI).strip()
# Must match MLflow server `--default-artifact-root` (e.g. docker-compose: s3://mlflow-artifacts/)
MLFLOW_ARTIFACT_BUCKET = (os.getenv("MLFLOW_S3_ARTIFACT_BUCKET") or "mlflow-artifacts").strip()
DATA_LAKE_BUCKET = "market-features"

# Configure MLflow
print(f"Connecting to MLflow at {MLFLOW_URI}...")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("ETF_Volatility_Prediction") 

print("MLflow connection successful")

# Configure MinIO Client
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS,
    aws_secret_access_key=MINIO_SECRET,
)


def ensure_bucket_exists(bucket_name: str) -> None:
    """Create the MinIO bucket if missing (same pattern as ETL for market-features)."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3_client.create_bucket(Bucket=bucket_name)


def train_model(ticker: str = "SPY") -> None:
    ensure_bucket_exists(MLFLOW_ARTIFACT_BUCKET)
    ensure_bucket_exists(DATA_LAKE_BUCKET)
    print(f"--- Starting Training Pipeline for {ticker} ---")
    
    # download data from data lake
    local_path = f"/tmp/{ticker}_features.parquet"
    print(f"Downloading {ticker} data from MinIO...")
    s3_client.download_file(DATA_LAKE_BUCKET, f"{ticker}_features.parquet", local_path)
    
    # load and prep data
    df = pd.read_parquet(local_path)
    
    # columns created in ETL
    features = ['log_return', 'RSI_14', 'MACD_12_26_9'] 
    
    # drop missing values before training
    df = df.dropna(subset=features + ['target_volatility_6h'])
    
    X = df[features]
    y = df['target_volatility_6h']
    
    # time-series split (no shuffling)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # start mlflow experiment run
    with mlflow.start_run(run_name=f"{ticker}_XGBoost_Baseline"):
        print("Training XGBoost Model...")
        
        # hyperparameters
        params = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 5,
            "random_state": 42
        }
        
        # log parameters so we can compare future versions
        mlflow.log_params(params)
        mlflow.log_param("ticker", ticker)
        
        # train the model
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)
        
        # predict & evaluate
        predictions = model.predict(X_test)
        rmse = math.sqrt(mean_squared_error(y_test, predictions))
        print(f"Model RMSE: {rmse:.5f}")
        
        # log the score and the physical model file to MLflow
        mlflow.log_metric("rmse", rmse)
        mlflow.xgboost.log_model(model, name="xgboost_model")
        
        print(f"Model successfully trained and logged to MLflow")

def run_training_pipeline() -> None:
    """Trains models for all ETFs. This is what Airflow will call."""
    tickers = ["SPY", "QQQ", "IWM"]
    for ticker in tickers:
        train_model(ticker)
    print("Training pipeline completed")

# for testing
if __name__ == "__main__":
    train_model("SPY")
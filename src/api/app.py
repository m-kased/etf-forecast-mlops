from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
import mlflow
import os
import pandas as pd
from dotenv import load_dotenv

from common.db import get_active_tickers

load_dotenv()

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

ml_models = {}

class PredictionInput(BaseModel):
    ticker: str
    log_return: float
    RSI_14: float
    MACD_12_26_9: float

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        upper_value = value.upper()
        valid = get_active_tickers()
        print(f"Valid tickers: {valid}")
        if upper_value not in valid:
            raise ValueError(f"Invalid ticker '{value}'. Valid tickers are: {', '.join(valid)}")
        return upper_value

def load_model_for_ticker(ticker: str) -> bool:
    registry_name = f"etf-vol-{ticker}"
    model_uri = f"models:/{registry_name}@champion"
    try:
        client = mlflow.MlflowClient()
        alias_info = client.get_model_version_by_alias(registry_name, "champion")
        ml_models[ticker] = mlflow.xgboost.load_model(model_uri)
        print(f"Loaded champion model for {ticker} (version {alias_info.version}) from registry.")
        return True
    except Exception as e:
        print(f"Failed to load champion model for {ticker}: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model_for_ticker("SPY")
    yield
    ml_models.clear()

app = FastAPI(title="ETF Volatility Inference API", lifespan=lifespan)

@app.get("/")
def health_check():
    return {
        "status": "healthy", 
        "loaded_models": list(ml_models.keys())
    }

@app.post("/predict")
def predict(data: PredictionInput):
    ticker = data.ticker
    
    if ticker not in ml_models:
        success = load_model_for_ticker(ticker)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Model for {ticker} could not be loaded or does not exist."
            )
    
    features = data.model_dump(exclude={"ticker"})
    input_df = pd.DataFrame([features])
    
    prediction = ml_models[ticker].predict(input_df)
    
    return {
        "ticker": ticker,
        "predicted_volatility": float(prediction[0])
    }
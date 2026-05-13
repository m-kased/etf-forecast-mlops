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
    print(f"Searching MLflow for the best {ticker} model...")
    try:
        experiment = mlflow.get_experiment_by_name("ETF_Volatility_Prediction") 
        if not experiment:
            raise ValueError("Experiment not found.")

        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"params.ticker = '{ticker}'",
            order_by=["metrics.rmse ASC"],
            max_results=1
        )
        
        if runs.empty:
            raise ValueError(f"No models found for {ticker}.")

        best_run_id = runs.iloc[0].run_id
        best_rmse = runs.iloc[0]["metrics.rmse"]
        
        print(f"found best model! Run ID: {best_run_id} | RMSE: {best_rmse:.5f}")

        model_uri = f"runs:/{best_run_id}/xgboost_model"
        
        ml_models[ticker] = mlflow.xgboost.load_model(model_uri)
        print(f"Model for {ticker} successfully loaded into memory.")
        return True
        
    except Exception as e:
        print(f"Failed to load model for {ticker}: {e}")
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
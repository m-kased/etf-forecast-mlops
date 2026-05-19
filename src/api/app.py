import logging
import os
from contextlib import asynccontextmanager

import mlflow
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, field_validator

from common.db import get_active_tickers
from common.metrics import (
    MODEL_RELOADS_TOTAL,
    MODELS_LOADED,
    PREDICTION_VOLATILITY,
    PREDICTIONS_TOTAL,
)

load_dotenv()

logger = logging.getLogger(__name__)

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

ml_models: dict[str, object] = {}
model_versions: dict[str, str] = {}


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
        if upper_value not in valid:
            raise ValueError(
                f"Invalid ticker '{value}'. Valid tickers are: {', '.join(valid)}"
            )
        return upper_value


def load_model_for_ticker(ticker: str) -> bool:
    registry_name = f"etf-vol-{ticker}"
    model_uri = f"models:/{registry_name}@champion"
    try:
        client = mlflow.MlflowClient()
        alias_info = client.get_model_version_by_alias(registry_name, "champion")
        ml_models[ticker] = mlflow.xgboost.load_model(model_uri)
        model_versions[ticker] = alias_info.version
        logger.info(
            "Loaded champion model for %s (version %s) from registry",
            ticker,
            alias_info.version,
        )
        return True
    except Exception as exc:
        logger.warning("Failed to load champion model for %s: %s", ticker, exc)
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    for ticker in get_active_tickers():
        load_model_for_ticker(ticker)
    MODELS_LOADED.set(len(ml_models))
    yield
    ml_models.clear()
    model_versions.clear()
    MODELS_LOADED.set(0)


app = FastAPI(title="ETF Volatility Inference API", lifespan=lifespan)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "loaded_models": {
            ticker: f"v{model_versions.get(ticker, '?')}" for ticker in ml_models
        },
    }


@app.post("/reload")
def reload_models(ticker: str | None = Query(default=None)):
    """Clear model cache and reload from registry.

    Called by Airflow after training promotes a new champion.
    - POST /reload          → reload all active tickers
    - POST /reload?ticker=SPY → reload only SPY
    """
    if ticker:
        ticker = ticker.upper()
        ml_models.pop(ticker, None)
        model_versions.pop(ticker, None)
        success = load_model_for_ticker(ticker)
        if not success:
            MODEL_RELOADS_TOTAL.labels(scope=ticker, status="error").inc()
            raise HTTPException(
                status_code=404, detail=f"No champion model found for {ticker}."
            )
        MODEL_RELOADS_TOTAL.labels(scope=ticker, status="success").inc()
        MODELS_LOADED.set(len(ml_models))
        return {"reloaded": [ticker], "version": model_versions.get(ticker)}

    ml_models.clear()
    model_versions.clear()
    reloaded = []
    for t in get_active_tickers():
        if load_model_for_ticker(t):
            reloaded.append(t)
    MODEL_RELOADS_TOTAL.labels(scope="all", status="success").inc()
    MODELS_LOADED.set(len(ml_models))
    return {
        "reloaded": reloaded,
        "versions": {t: model_versions.get(t) for t in reloaded},
    }


@app.post("/predict")
def predict(data: PredictionInput):
    ticker = data.ticker

    if ticker not in ml_models:
        success = load_model_for_ticker(ticker)
        if not success:
            PREDICTIONS_TOTAL.labels(ticker=ticker, status="model_missing").inc()
            raise HTTPException(
                status_code=404,
                detail=f"Model for {ticker} could not be loaded or does not exist.",
            )
        MODELS_LOADED.set(len(ml_models))

    features = data.model_dump(exclude={"ticker"})
    input_df = pd.DataFrame([features])

    try:
        prediction = ml_models[ticker].predict(input_df)
        volatility = float(prediction[0])
    except Exception:
        PREDICTIONS_TOTAL.labels(ticker=ticker, status="error").inc()
        raise

    PREDICTIONS_TOTAL.labels(ticker=ticker, status="success").inc()
    PREDICTION_VOLATILITY.labels(ticker=ticker).observe(volatility)

    return {
        "ticker": ticker,
        "predicted_volatility": volatility,
    }

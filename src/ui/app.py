import streamlit as st
import requests
import os
from common.db import get_active_tickers

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="ETF Volatility Predictor", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("ETF Volatility Predictor")
st.write("Enter the market indicators to predict the next-day volatility.")

with st.expander("How to use this tool"):
    st.write("This model predicts the next-day volatility of an ETF using Machine Learning.")
    st.write("Use the input fields below to set the financial indicators. Hover over the '?' icon next to each input for specific definitions.")

active_tickers = get_active_tickers()
if not active_tickers:
    st.warning("Could not load tickers from the database. Defaulting to SPY.")
    active_tickers = ["SPY"]

ticker = st.selectbox("Select ETF Ticker", active_tickers)

col1, col2, col3 = st.columns(3)
with col1:
    log_return = st.number_input(
        "Log Return",
        value=0.0010,
        format="%.5f",
        help="Natural log of today's price / yesterday's price. Positive = up, negative = down.",
    )
with col2:
    rsi_14 = st.number_input(
        "RSI (14-day)",
        value=55.5,
        format="%.2f",
        help="Relative Strength Index over 14 days. Ranges 0–100; above 70 = overbought, below 30 = oversold.",
    )
with col3:
    macd = st.number_input(
        "MACD (12,26,9)",
        value=0.020,
        format="%.3f",
        help="Moving Average Convergence Divergence (12-day EMA minus 26-day EMA, signal line 9). Positive = bullish momentum.",
    )

if st.button("Predict Volatility"):
    payload = {
        "ticker": ticker,
        "log_return": log_return,
        "RSI_14": rsi_14,
        "MACD_12_26_9": macd
    }
    
    with st.spinner(f"Requesting prediction for {ticker}..."):
        try:
            response = requests.post(f"{API_URL}/predict", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                pred_vol = result["predicted_volatility"]
                
                st.success("Prediction successful!")
                st.metric(label=f"Predicted Volatility ({ticker})", value=f"{pred_vol:.4%}")
                
                intensity = min(pred_vol / 0.05, 1.0) 
                st.write("Volatility Intensity:")
                st.progress(intensity)
                
                st.session_state.history.append({
                    "Ticker": ticker,
                    "Log Return": log_return,
                    "RSI": rsi_14,
                    "MACD": macd,
                    "Predicted Vol": f"{pred_vol:.4%}"
                })
            else:
                st.error(f"API Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Failed to connect to the API: {e}")

if st.session_state.history:
    st.divider()
    st.subheader("Prediction History")
    st.dataframe(st.session_state.history, use_container_width=True)
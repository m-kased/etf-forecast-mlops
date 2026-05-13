"""Shared database utilities — single source of truth for ticker config."""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql://admin:admin123@localhost:5432/ml_data"


def get_database_url() -> str:
    return (os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL).strip()


def get_active_tickers() -> list[str]:
    """Fetch all active ticker symbols from the tickers table."""
    try:
        conn = psycopg2.connect(get_database_url())
        print("Database connected successfully")
    except:
        print("Database not connected successfully")
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT symbol FROM tickers WHERE is_active = TRUE ORDER BY symbol"
            )
            rows = cur.fetchall()
            return [row[0] for row in rows]
    finally:
        conn.close()

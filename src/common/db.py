"""Shared database utilities — single source of truth for ticker config."""

import logging
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error as Psycopg2Error

load_dotenv()

logger = logging.getLogger(__name__)

# Local/docker-compose default; production uses DATABASE_URL from secrets.
DEFAULT_DATABASE_URL = "postgresql://admin:admin123@localhost:5432/ml_data"


def get_database_url() -> str:
    return (os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL).strip()


def get_active_tickers() -> list[str]:
    """Fetch all active ticker symbols from the tickers table."""
    try:
        conn = psycopg2.connect(get_database_url())
    except Psycopg2Error as exc:
        logger.warning("Database connection failed: %s", exc)
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

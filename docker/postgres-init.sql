-- PostgreSQL initialization script
-- Runs once on first container start (when data directory is empty)
-- Creates all databases and users needed by the ML platform

-- Airflow metadata database
CREATE DATABASE airflow;

-- MLflow experiment tracking database
CREATE DATABASE mlflow;

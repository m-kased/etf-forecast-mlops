FROM python:3.12-slim

# Install uv binary globally
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a non-root user with a standard user ID
RUN useradd -m -u 1000 appuser

# Create the working directory and give ownership to the new user
WORKDIR /app
RUN chown appuser:appuser /app

# Switch to the secure user
USER appuser

# Set up the cache directory
ENV UV_CACHE_DIR=/home/appuser/.cache/uv

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Create a virtual environment and add it to the system path
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install API dependencies using the cache and appuser ID
RUN --mount=type=cache,id=uv-api-cache,target=${UV_CACHE_DIR},uid=1000 \
    uv pip install -r pyproject.toml --extra api

# Copy the API source code
COPY --chown=appuser:appuser src/api/ src/api/

# Set Python path
ENV PYTHONPATH="/app"

# Run Uvicorn server
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
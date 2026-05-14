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

# Install UI dependencies using the cache and appuser ID
RUN --mount=type=cache,id=uv-ui-cache,target=${UV_CACHE_DIR},uid=1000 \
    uv pip install -r pyproject.toml --extra ui

# Copy the source code and the common folder
COPY --chown=appuser:appuser src/ui/ /app/src/ui/
COPY --chown=appuser:appuser src/common/ src/common/

# Set Python path so `from common.db import ...` resolves
ENV PYTHONPATH="/app/src:/app"

# Run Streamlit on the standard port 8501
CMD ["streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
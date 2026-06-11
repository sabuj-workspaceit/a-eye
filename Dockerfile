# Stage 1: Builder - Install dependencies with Poetry
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency definition files
COPY pyproject.toml ./

# Install dependencies into a virtual environment
# --no-root: Don't install the project itself, only dependencies
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --sync

# Stage 2: Runner - Create the final application image
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/.venv .venv
ENV PATH="/app/.venv/bin:$PATH"

COPY ./app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Scaffold image for Sluice-api — service not implemented yet.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
CMD ["python", "-m", "Sluice_api.main"]

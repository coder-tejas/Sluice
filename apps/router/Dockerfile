FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY sluice_router ./sluice_router
RUN pip install --no-cache-dir .
EXPOSE 8001
CMD ["uvicorn", "sluice_router.main:app", "--host", "0.0.0.0", "--port", "8001"]

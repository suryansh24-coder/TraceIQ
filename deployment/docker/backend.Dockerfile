# Redirects to the main backend Dockerfile
# To build from the root context:
# docker build -t traceiq-backend -f deployment/docker/backend.Dockerfile .

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd -m traceiq
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN chown -R traceiq:traceiq /app
USER traceiq

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

.PHONY: install dev test lint format docker-build docker-run

install:
	cd backend && pip install -r requirements.txt

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && pytest

lint:
	cd backend && ruff check .

format:
	cd backend && ruff check --fix . && ruff format .

docker-build:
	docker build -t traceiq-backend -f backend/Dockerfile backend

docker-run:
	docker run -p 8000:8000 --env-file .env traceiq-backend

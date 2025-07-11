.PHONY: build up down logs shell test test-unit test-integration test-all

build:
	docker compose build

build-no-cache:
	docker compose build --no-cache

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec app /bin/bash

# MVP Testing Commands
test: test-unit
	pytest tests/unit/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v --cov=src --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v

test-all:
	pytest tests/ -v --cov=src --cov-report=term-missing

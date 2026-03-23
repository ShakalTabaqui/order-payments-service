.PHONY: help up down restart ps logs build smoke lint test check clean

DC = docker compose
API_PORT ?= 8000

help:
	@echo "Targets:"
	@echo "  up       - поднять сервисы (API_PORT=$(API_PORT))"
	@echo "  down     - остановить сервисы"
	@echo "  restart  - пересоздать контейнеры"
	@echo "  ps       - статус контейнеров"
	@echo "  logs     - логи"
	@echo "  build    - собрать образ api"
	@echo "  smoke    - прогнать smoke-тест"
	@echo "  lint     - flake8 (в контейнере)"
	@echo "  test     - pytest (в контейнере)"
	@echo "  check    - lint + test"
	@echo "  clean    - down + удалить volume"

up:
	API_PORT=$(API_PORT) $(DC) up -d --build

down:
	$(DC) down

restart:
	API_PORT=$(API_PORT) $(DC) up -d --build --force-recreate

ps:
	API_PORT=$(API_PORT) $(DC) ps

logs:
	API_PORT=$(API_PORT) $(DC) logs -f --tail 200

build:
	$(DC) build api

smoke:
	API_PORT=$(API_PORT) ./smoke.sh

lint:
	$(DC) run --rm api python -m flake8

test:
	$(DC) run --rm api python -m pytest -q

check: lint test

clean:
	$(DC) down -v

# Un cortado, por favor — monorepo orchestration.
# The engine runs as a subprocess of the API (shared filesystem), so local
# bring-up is host processes, not containers; Docker images belong to the
# CD phase (docs/ci-cd-plan.md Phase 4).

API_PORT ?= 8000
FRONT_PORT ?= 3000

.PHONY: help up e2e-smoke e2e-full test test-engine test-api test-frontend

help: ## List available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'

up: ## Boot Laravel + queue worker + Nuxt for manual testing (Ctrl-C stops all)
	@API_PORT=$(API_PORT) FRONT_PORT=$(FRONT_PORT) ./scripts/dev-up.sh

e2e-smoke: ## Automated smoke across the three processes (search via real engine)
	@API_PORT=$(API_PORT) FRONT_PORT=$(FRONT_PORT) ./scripts/e2e-smoke.sh

e2e-full: ## Smoke + a real generate job to completion (downloads + ffmpeg, slow)
	@E2E_FULL=1 API_PORT=$(API_PORT) FRONT_PORT=$(FRONT_PORT) ./scripts/e2e-smoke.sh

test: test-engine test-api test-frontend ## Run the three test suites

test-engine: ## Engine unit tests (pytest)
	cd engine && python3 -m pytest -q

test-api: ## API tests (Pest)
	cd api && ./vendor/bin/pest

test-frontend: ## Frontend tests (Vitest)
	cd frontend && pnpm test

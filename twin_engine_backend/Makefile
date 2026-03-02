# ==============================================================
# TwinEngine Backend — Makefile
# Common commands for development, data management, and deployment
# ==============================================================

PYTHON  = python
MANAGE  = $(PYTHON) manage.py
VENV    = source venv/bin/activate

.PHONY: help run migrate makemigrations check test \
        db-backup db-restore db-flush db-seed db-reset \
        static superuser shell lint

# ------ Help ------
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ------ Development ------
run: ## Start development server (Daphne ASGI)
	$(MANAGE) runserver

run-asgi: ## Start Daphne ASGI server (WebSocket support)
	daphne -b 0.0.0.0 -p 8000 twinengine_core.asgi:application

shell: ## Open Django shell
	$(MANAGE) shell

superuser: ## Create a superuser
	$(MANAGE) createsuperuser

check: ## Run Django system checks
	$(MANAGE) check

check-deploy: ## Run deployment checks (simulates DEBUG=False)
	DEBUG=False $(MANAGE) check --deploy

# ------ Database ------
migrate: ## Apply database migrations
	$(MANAGE) migrate

makemigrations: ## Create new migration files
	$(MANAGE) makemigrations

db-backup: ## Export all app data to timestamped JSON backup
	$(MANAGE) export_data --include-auth

db-backup-named: ## Export data to a named file (usage: make db-backup-named FILE=my_backup.json)
	$(MANAGE) export_data --include-auth -o $(FILE)

db-restore: ## Import data from a JSON fixture (usage: make db-restore FILE=backup.json)
	$(MANAGE) import_data $(FILE)

db-restore-flush: ## Flush DB then import (usage: make db-restore-flush FILE=backup.json)
	$(MANAGE) import_data $(FILE) --flush

db-flush: ## Flush all data (destructive!)
	$(MANAGE) flush

db-seed: ## Load full demo data
	$(MANAGE) create_full_demo_data

db-seed-users: ## Create demo users only
	$(MANAGE) create_demo_users

db-reset: ## Reset DB: flush → migrate → seed demo data
	$(MANAGE) flush --no-input
	$(MANAGE) migrate
	$(MANAGE) create_full_demo_data

db-check-waits: ## Check for tables with long wait times
	$(MANAGE) check_wait_times

# ------ Static Files ------
static: ## Collect static files
	$(MANAGE) collectstatic --no-input

# ------ Testing ------
test: ## Run all tests
	$(MANAGE) test --verbosity=2

test-app: ## Run tests for a specific app (usage: make test-app APP=order_engine)
	$(MANAGE) test apps.$(APP) --verbosity=2

test-signals: ## Run table status signal tests
	$(MANAGE) test apps.order_engine.tests.test_table_status --verbosity=2

# ------ Requirements ------
install: ## Install Python dependencies
	pip install -r requirements.txt

freeze: ## Freeze current packages to requirements
	pip freeze > requirements.lock.txt

.PHONY: help build up down logs clean test install dev prod migrate backup restore

# Colors for help text
CYAN := \033[36m
RESET := \033[0m
BOLD := \033[1m

help: ## Show this help message
	@echo "$(BOLD)Intelligent Store Migration Assistant$(RESET)"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'

# Development commands
install: ## Install dependencies for development
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev: ## Start development environment
	docker-compose up -d postgres redis
	@echo "Waiting for services to be ready..."
	sleep 5
	@echo "Starting development servers..."
	docker-compose up backend frontend

up: ## Start all services in development mode
	docker-compose up -d

prod: ## Start all services in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f postgres

# Database commands
migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create NAME=description)
	docker-compose exec backend alembic revision --autogenerate -m "$(NAME)"

migrate-down: ## Downgrade database migration
	docker-compose exec backend alembic downgrade -1

db-reset: ## Reset database (WARNING: This will delete all data)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	docker-compose exec backend alembic upgrade head

# Build commands
build: ## Build all Docker images
	docker-compose build

build-backend: ## Build backend Docker image
	docker-compose build backend

build-frontend: ## Build frontend Docker image
	docker-compose build frontend

# Testing commands
test: ## Run all tests
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend: ## Run backend tests
	docker-compose exec backend pytest -v

test-frontend: ## Run frontend tests
	docker-compose exec frontend npm test

test-coverage: ## Run tests with coverage
	docker-compose exec backend pytest --cov=app --cov-report=html
	docker-compose exec frontend npm run test:coverage

lint: ## Run linting for all code
	$(MAKE) lint-backend
	$(MAKE) lint-frontend

lint-backend: ## Run backend linting
	docker-compose exec backend flake8 app/
	docker-compose exec backend black --check app/
	docker-compose exec backend isort --check-only app/

lint-frontend: ## Run frontend linting
	docker-compose exec frontend npm run lint

format: ## Format all code
	$(MAKE) format-backend
	$(MAKE) format-frontend

format-backend: ## Format backend code
	docker-compose exec backend black app/
	docker-compose exec backend isort app/

format-frontend: ## Format frontend code
	docker-compose exec frontend npm run lint -- --fix

# Monitoring commands
monitoring-up: ## Start monitoring services (Grafana, Prometheus)
	docker-compose up -d prometheus grafana

monitoring-down: ## Stop monitoring services
	docker-compose stop prometheus grafana

# Data management
backup: ## Create database backup
	@echo "Creating backup..."
	docker-compose exec postgres pg_dump -U migration_user migration_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created successfully"

restore: ## Restore database from backup (usage: make restore FILE=backup.sql)
	@echo "Restoring from $(FILE)..."
	docker-compose exec -T postgres psql -U migration_user migration_db < $(FILE)
	@echo "Restore completed"

# Cleanup commands
clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up everything including images
	docker-compose down -v --rmi all
	docker system prune -af
	docker volume prune -f

# Security scanning
security-scan: ## Run security scans
	docker-compose exec backend safety check
	docker-compose exec frontend npm audit

# Deployment commands
deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Utility commands
shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

shell-db: ## Open database shell
	docker-compose exec postgres psql -U migration_user migration_db

# Performance testing
load-test: ## Run load tests
	docker-compose exec backend locust -f tests/load/locustfile.py --host=http://localhost:8000

# Documentation
docs: ## Generate API documentation
	docker-compose exec backend python -m app.utils.generate_docs

# Default target
.DEFAULT_GOAL := help
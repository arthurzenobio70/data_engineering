.PHONY: help install install-dev test lint format check clean deploy destroy

# Variables
PYTHON_VERSION = 3.11
PROJECT_NAME = stock-market-pipeline

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project dependencies
	@echo "Installing dependencies..."
	uv sync

install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	uv sync --extra dev

install-all: ## Install all dependencies (including Airflow)
	@echo "Installing all dependencies..."
	uv sync --extra all

lint: ## Run linting (ruff)
	@echo "Running linting..."
	uv run ruff check .

lint-fix: ## Run linting with automatic fixes
	@echo "Running linting with automatic fixes..."
	uv run ruff check . --fix

format: ## Format code with black
	@echo "Formatting code..."
	uv run black .

type-check: ## Check types with mypy
	@echo "Checking types..."
	uv run mypy dags/ dataproc_jobs/

check: lint type-check ## Run all quality checks
	@echo "All checks completed!"

pre-commit-install: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	@echo "Running pre-commit..."
	uv run pre-commit run --all-files

clean: ## Remove temporary files
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

# Infrastructure commands
tf-init: ## Initialize Terraform
	@echo "Initializing Terraform..."
	cd terraform && terraform init

tf-plan: ## Display Terraform plan
	@echo "Generating Terraform plan..."
	cd terraform && terraform plan

tf-apply: ## Apply Terraform changes
	@echo "Applying Terraform changes..."
	cd terraform && terraform apply

tf-destroy: ## Destroy infrastructure
	@echo "Destroying infrastructure..."
	cd terraform && terraform destroy

# Docker commands
docker-build: ## Build Docker images
	@echo "Building Docker images..."
	docker-compose build

docker-dev: ## Start development environment
	@echo "Starting development environment..."
	docker-compose --profile dev up -d

docker-local-test: ## Start local testing environment
	@echo "Starting local testing environment..."
	docker-compose --profile local-test up -d

docker-jupyter: ## Start Jupyter notebook
	@echo "Starting Jupyter notebook..."
	docker-compose --profile jupyter up -d

docker-dev-test: ## Start pipeline development testing environment
	@echo "Starting pipeline development testing environment..."
	docker-compose --profile dev-test up -d

docker-stop: ## Stop all containers
	@echo "Stopping all containers..."
	docker-compose down

docker-clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development commands
dev-setup: install-dev pre-commit-install ## Initial setup for development
	@echo "Development environment configured!"

test: ## Run tests
	@echo "Running tests..."
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-docker: ## Run tests in Docker container
	@echo "Running tests in Docker..."
	docker-compose --profile test run --rm test-runner

validate: check test ## Validate code before commit
	@echo "Complete validation!"

# Pipeline commands
upload-erp: ## Upload ERP file to GCS
	@echo "Uploading ERP file..."
	gsutil cp data/erp_companies.csv gs://datalake-stock-market-bucket/raw/ERP/

# Utilities
env-info: ## Show environment information
	@echo "Environment information:"
	@echo "Python: $(shell python --version)"
	@echo "uv: $(shell uv --version)"
	@echo "Directory: $(shell pwd)"
	@echo "Python files:"
	@find . -name "*.py" | head -10

add-dep: ## Add new dependency (use: make add-dep PACKAGE=package-name)
	@echo "Adding dependency: $(PACKAGE)"
	uv add $(PACKAGE)

add-dev-dep: ## Add development dependency
	@echo "Adding development dependency: $(PACKAGE)"
	uv add --dev $(PACKAGE)

cleanup-v1: ## Clean up v1 files and promote v2 to main versions
	@echo "Cleaning up v1 files..."
	@powershell -ExecutionPolicy Bypass -File cleanup_v1_files.ps1 
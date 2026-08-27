.PHONY: setup dev test test-backend test-frontend lint format clean docker-up docker-down

setup:
	@echo "Setting up development environment..."
	cd apps/api && python -m pip install -r requirements.txt
	cd apps/web && npm install

dev:
	@echo "Starting local development servers..."
	docker-compose up -d db redis
	@echo "DB and Redis started in background. Starting API and Web..."
	concurrently "cd apps/api && uvicorn app.main:app --reload --port 8000" "cd apps/web && npm run dev"

test: test-backend test-frontend

test-backend:
	@echo "Running backend unit and integration tests..."
	cd apps/api && python -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd apps/web && npm test

lint:
	@echo "Running linters..."
	cd apps/api && flake8 app tests
	cd apps/web && npm run lint

format:
	@echo "Formatting codebase..."
	cd apps/api && black app tests
	cd apps/web && npm run format

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf apps/web/.next apps/web/out

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down -v

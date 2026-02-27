# MindWall — Cognitive Firewall
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
# https://github.com/vrip7

.PHONY: dev prod build down logs clean test lint

# Development
dev:
	docker compose -f docker-compose.yml -f docker-compose.override.yml up --build

# Production
prod:
	docker compose up -d --build

# Build all services
build:
	docker compose build

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# View logs for a specific service
logs-%:
	docker compose logs -f $*

# Clean everything
clean:
	docker compose down -v --rmi all --remove-orphans
	rm -rf data/db/mindwall.db

# Run API tests
test:
	cd api && python -m pytest tests/ -v

# Lint
lint:
	cd api && python -m ruff check .
	cd proxy && python -m ruff check .

# Setup (first-time)
setup:
	bash setup.sh

# Pull LLM model
pull-model:
	docker compose exec ollama ollama pull llama3.1:8b

# Create Ollama Modelfile and load fine-tuned model
load-model:
	docker compose exec ollama ollama create mindwall-llama3.1-8b -f /root/.ollama/Modelfile

# Database reset
db-reset:
	rm -f data/db/mindwall.db
	docker compose restart api

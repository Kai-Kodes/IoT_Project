# ============================================================
# P_311 Makefile - Industrial IoT Fault Diagnosis Assistant
# ============================================================

.PHONY: all setup run stop test demo clean docker-up docker-down

all: run

setup:
	@echo "Setting up Python virtual environment..."
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "Setting up Frontend..."
	cd frontend && npm install && npm run build
	@echo "Setup complete!"

run:
	@./scripts/start_all.sh

stop:
	@./scripts/stop_all.sh

tunnel:
	@./scripts/start_tunnel.sh

stop-tunnel:
	@./scripts/stop_tunnel.sh


test:
	@.venv/bin/pytest backend/tests -v

demo:
	@.venv/bin/python scripts/run_demo.py

dataset:
	@.venv/bin/python simulator/dataset_generator.py

experiments:
	@.venv/bin/python experiments/run_all_experiments.py

frontend-dev:
	@cd frontend && npm run dev

docker-up:
	@docker compose up -d

docker-down:
	@docker compose down

clean:
	@./scripts/stop_all.sh 2>/dev/null || true
	@rm -rf data/*.db* data/vector_store/*.npy data/vector_store/*.json logs/*.log logs/*.pid
	@echo "Cleaned database, logs, and temporary caches."

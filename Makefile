.PHONY: setup run run-dry test lint clean help

help:
	@echo "Pipeline Automatisé - Commandes disponibles:"
	@echo "  make setup     - Installer les dépendances"
	@echo "  make run       - Lancer le pipeline"
	@echo "  make run-dry   - Lancer en mode dry-run (pas de sauvegarde/alerte)"
	@echo "  make test      - Lancer les tests"
	@echo "  make lint      - Vérifier et formater le code"
	@echo "  make clean     - Nettoyer les fichiers générés"

setup:
	uv sync
	@echo "✓ Dépendances installées"

run:
	uv run python src/main.py

run-dry:
	uv run python src/main.py --dry-run

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	uv run ruff check src/ tests/
	uv run ruff format src/ tests/

lint-fix:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f .coverage 2>/dev/null || true

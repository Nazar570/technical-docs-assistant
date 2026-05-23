PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest
UVICORN := .venv/bin/uvicorn
PRE_COMMIT := .venv/bin/pre-commit

.PHONY: setup lint format typecheck test run clean

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PRE_COMMIT) install

lint:
	$(RUFF) check src tests

format:
	$(RUFF) format src tests

typecheck:
	$(MYPY) src tests

test:
	PYTHONPATH=. $(PYTEST)

run:
	PYTHONPATH=. $(UVICORN) src.api.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

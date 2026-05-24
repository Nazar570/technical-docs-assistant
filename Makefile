PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest
UVICORN := .venv/bin/uvicorn
PRE_COMMIT := .venv/bin/pre-commit

.PHONY: setup lint format typecheck test run clean evaluate experiment frontend

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

evaluate:
	export GEMINI_API_KEY=$$(grep GEMINI_API_KEY .env | cut -d '=' -f2 | tr -d '"') && \
	PYTHONPATH=. $(PYTHON) scripts/evaluate_rag.py

experiment:
	PYTHONPATH=. $(PYTHON) scripts/run_experiment.py

frontend:
	STREAMLIT_SERVER_HEADLESS=true PYTHONPATH=. $(PYTHON) -m streamlit run src/frontend/app.py --server.port 8501

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

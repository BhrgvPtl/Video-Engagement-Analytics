DATA_RAW := data/raw
DATA_PROC := data/processed

.PHONY: install build model run clean test

install:
	@echo "Using requirements.txt; run: pip install -r requirements.txt"

build:
	python -m src.ingest
	python -m src.clean
	python -m src.simulate_watch
	python -m src.features

model:
	python -m src.churn_model

run:
	streamlit run streamlit_app.py

clean:
	powershell -Command "if (Test-Path '$(DATA_PROC)') { Remove-Item -Recurse -Force '$(DATA_PROC)' }; New-Item -ItemType Directory -Force '$(DATA_PROC)' | Out-Null"

test:
	@echo "No tests configured"

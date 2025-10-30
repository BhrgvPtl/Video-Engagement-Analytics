DATA_RAW=data/raw
DATA_PROC=data/processed

<<<<<<< Updated upstream
install:
@echo "Dependencies rely on the Python standard library."

build:
python -m src.utils

run:
@echo "Launch the Streamlit dashboard after installing optional dependencies."

test:
python -m unittest discover -s tests
=======
.PHONY: build model run clean

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
	@if exist $(DATA_PROC) rmdir /S /Q $(DATA_PROC) || true
	@mkdir $(DATA_PROC) 2>nul || true
>>>>>>> Stashed changes

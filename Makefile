.PHONY: install build run test

install:
	poetry install

build:
	poetry run python -m src.utils

run:
	poetry run streamlit run dashboards/streamlit_app.py --server.port=8501

test:
	poetry run pytest

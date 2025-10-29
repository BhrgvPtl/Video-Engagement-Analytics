.PHONY: install build run test

install:
@echo "Dependencies rely on the Python standard library."

build:
python -m src.utils

run:
@echo "Launch the Streamlit dashboard after installing optional dependencies."

test:
python -m unittest discover -s tests

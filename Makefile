.PHONY: install transform load validate trend percentage rolling test lint pipeline

install:
	python -m pip install -r requirements.txt

transform:
	python -m src.etl.transform_mrts

load:
	python -m src.etl.load_mrts

validate:
	python -m src.etl.test_mrts_queries

trend:
	python -m src.analysis.trend_analysis

percentage:
	python -m src.analysis.percentage_change

rolling:
	python -m src.analysis.rolling_window

pipeline: transform load validate

test:
	pytest -q

lint:
	ruff check src tests

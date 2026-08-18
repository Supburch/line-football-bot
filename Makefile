.PHONY: run test lint format

run:
	gunicorn run:app --bind 0.0.0.0:10000 --workers 1 --threads 8

test:
	pytest -v

lint:
	ruff check .

format:
	black .

format-check:
	black --check .

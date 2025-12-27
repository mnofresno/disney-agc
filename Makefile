.PHONY: test lint format clean install install-dev

test:
	pytest

test-cov:
	pytest --cov=chromecast_agc --cov-report=html

lint:
	flake8 chromecast_agc tests --max-line-length=127 --ignore=E501,W503
	black --check chromecast_agc tests
	isort --check-only chromecast_agc tests

format:
	black chromecast_agc tests
	isort chromecast_agc tests

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	@poetry run pytest --cov=ggmail --cov-config .coveragerc --cov-report=xml --cov-report=term tests/

format:
	@poetry run black ggmail tests
	@poetry run isort ggmail tests
	@poetry run flake8 ggmail tests

check:
	@poetry run black ggmail tests --check
	@poetry run isort ggmail tests --check
	@poetry run flake8 ggmail tests
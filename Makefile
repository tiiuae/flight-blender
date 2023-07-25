# Building commands
build:
	docker-compose build

rebuild:
	docker-compose build --no-cache

# Linting commands
lint:
	ruff .
	isort .
	black .



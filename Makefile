PYTHON ?= python3

.PHONY: install-dev test lint check secrets verify

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	ruff check git-create tests

check:
	./git-create --no-color check --offline

secrets:
	./git-create --no-color secrets .

verify: lint test check secrets

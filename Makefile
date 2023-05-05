SHELL := /bin/bash
PYTHON := $(shell command -v python3 >/dev/null 2>&1 && echo python3 || echo python)

install: ## [Local development] Upgrade pip, install requirements, install package.
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -e . && \
	pip install pip-tools && \
	pip-compile requirements.in && \
	pip install -r requirements.txt

.PHONY: test
test:
	pytest --verbose
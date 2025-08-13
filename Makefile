.PHONY: install reinstall setup test clean-setup setup_docs setup_publish build_docs docs publish

install:
	pip install . --quiet

reinstall:
	pip uninstall tc_aws -y
	pip install . --quiet

# Cached setup to avoid reinstalling dependencies on every test run
DEPS_DIR := .deps
SETUP_STAMP := $(DEPS_DIR)/tests.ok

$(DEPS_DIR):
	mkdir -p $(DEPS_DIR)

$(SETUP_STAMP): setup.py version.txt tests/requirements.txt | $(DEPS_DIR)
	pip install -e .
	pip install -r tests/requirements.txt
	touch $(SETUP_STAMP)

setup: $(SETUP_STAMP)

clean-setup:
	rm -rf $(DEPS_DIR)

setup_docs:
	pip install -r docs/requirements.txt

setup_publish:
	pip install -r publish_requirements.txt

build_docs:
	cd docs && make html

docs: setup_docs build_docs
	python -mwebbrowser file:///`pwd`/docs/_build/html/index.html

test:
	pytest

publish: setup_publish
	python setup.py sdist
	twine upload dist/*

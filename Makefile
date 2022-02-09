.PHONY: install reinstall setup test

install:
	pip install . --quiet

reinstall:
	pip uninstall tc_aws -y
	pip install . --quiet

setup:
	pip install -e .[tests]

setup_docs:
	pip install -r docs/requirements.txt

setup_publish:
	pip install -r publish_requirements.txt

build_docs:
	cd docs && make html

docs: setup_docs build_docs
	python -mwebbrowser file:///`pwd`/docs/_build/html/index.html

test: setup
	pytest

publish: setup_publish
	python setup.py sdist
	twine upload dist/*

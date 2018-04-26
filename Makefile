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

build_docs:
	cd docs && make html

docs: setup_docs build_docs
	python -mwebbrowser file:///`pwd`/docs/_build/html/index.html

test: setup
	pyvows -c -l tc_aws

publish:
	python setup.py register -r pypi
	python setup.py sdist upload -r pypi

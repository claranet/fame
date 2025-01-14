.DEFAULT_GOAL := install

install:
	@mise install
	@pre-commit install
	@poetry install

check:
	@poetry run tox -e lint
	@pre-commit run --all-files

update:
	@poetry update
	@poetry lock
	@pre-commit autoupdate

update-tooling:
	@copier update --trust --skip-answered --answers-file .copier-python-poetry-answers.yml

test:
	# Running tests
	@poetry run tox

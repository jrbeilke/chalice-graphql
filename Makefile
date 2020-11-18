dev-setup:
	python pip install -e ".[test]"

tests:
	py.test tests --cov=chalice_graphql -vv
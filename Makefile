.PHONY: lint test verify

lint:
	python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"
	python3 scripts/check_legacy_fitbit.py

test:
	python2 tests/test_fitbit_oauth_request.py

verify: lint test

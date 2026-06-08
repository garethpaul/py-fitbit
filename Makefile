.PHONY: check docs lint test verify

docs:
	test -f docs/plans/2026-06-08-py-fitbit-baseline.md
	grep -q "Status: Completed" docs/plans/2026-06-08-py-fitbit-baseline.md
	grep -q "make check" docs/plans/2026-06-08-py-fitbit-baseline.md

lint:
	python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"
	python3 scripts/check_legacy_fitbit.py

test:
	python2 tests/test_fitbit_oauth_request.py

verify: lint test docs

check: verify

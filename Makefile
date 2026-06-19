.PHONY: check build docs lint test verify

docs:
	@for plan in docs/plans/*.md; do \
		test -f "$$plan"; \
		grep -q "Status: Completed" "$$plan"; \
		grep -q "make check" "$$plan"; \
	done

lint:
	python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"
	python3 scripts/check_legacy_fitbit.py
	PYTHONDONTWRITEBYTECODE=1 python3 tests/test_checker_integrity.py

test:
	PYTHONDONTWRITEBYTECODE=1 python2 tests/test_settings.py
	PYTHONDONTWRITEBYTECODE=1 python2 tests/test_fitbit_oauth_request.py

build: test

verify: lint test build docs

check: verify

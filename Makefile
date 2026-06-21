.PHONY: check build docs lint root-test test verify

ifneq ($(origin MAKEFILE_LIST),file)
$(error MAKEFILE_LIST must not be overridden)
endif
override REPO_ROOT := $(shell path='$(subst ','"'"',$(MAKEFILE_LIST))'; path=$$(printf '%s' "$$path" | /usr/bin/sed 's/^ //'); directory=$$(/usr/bin/dirname -- "$$path"); CDPATH= cd -- "$$directory" && /bin/pwd -P)

docs:
	@cd "$(REPO_ROOT)" && for plan in docs/plans/*.md; do \
		test -f "$$plan"; \
		grep -q "Status: Completed" "$$plan"; \
		grep -q "make check" "$$plan"; \
	done

lint:
	cd "$(REPO_ROOT)" && python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"
	cd "$(REPO_ROOT)" && python3 -c "import py_compile; [py_compile.compile(path, cfile='/tmp/py-fitbit-' + path.replace('/', '-') + '.pyc', doraise=True) for path in ('fitbit.py', 'settings.py', 'tests/test_fitbit_oauth_request.py', 'tests/test_settings.py')]"
	cd "$(REPO_ROOT)" && python3 scripts/check_legacy_fitbit.py
	cd "$(REPO_ROOT)" && PYTHONDONTWRITEBYTECODE=1 python3 tests/test_checker_integrity.py

test:
	cd "$(REPO_ROOT)" && PYTHONDONTWRITEBYTECODE=1 python2 tests/test_settings.py
	cd "$(REPO_ROOT)" && PYTHONDONTWRITEBYTECODE=1 python2 tests/test_fitbit_oauth_request.py
	cd "$(REPO_ROOT)" && PYTHONDONTWRITEBYTECODE=1 python3 tests/test_settings.py
	cd "$(REPO_ROOT)" && PYTHONDONTWRITEBYTECODE=1 python3 tests/test_fitbit_oauth_request.py

build: test

root-test:
	cd "$(REPO_ROOT)" && scripts/test-makefile-root.sh

verify: lint test build docs root-test

check: verify

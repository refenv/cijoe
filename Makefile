DOC_BUILD_DIR=build
PROJECT_NAME=cijoe
PROJECT_VERSION_MAJOR=$(shell grep "VERSION_MAJOR = ." modules/cij/__init__.py | cut -d " " -f 3)
PROJECT_VERSION_MINOR=$(shell grep "VERSION_MINOR = ." modules/cij/__init__.py | cut -d " " -f 3)
PROJECT_VERSION_PATCH=$(shell grep "VERSION_PATCH = ." modules/cij/__init__.py | cut -d " " -f 3)
PROJECT_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}
NEXT_VERSION_PATCH=$$((${PROJECT_VERSION_PATCH} + 1))
NEXT_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${NEXT_VERSION_PATCH}

INSTALL_OPTS?=

.PHONY: user
user:
	$(eval INSTALL_OPTS := --user)

.PHONY: install
install:
	pip install . $(INSTALL_OPTS)

.PHONY: uninstall
uninstall:
	pip uninstall ${PROJECT_NAME} --yes || true

.PHONY: dev
dev: uninstall install selftest-view
	@echo -n "# dev: "; date

.PHONY: bump
bump:
	@echo "# Bumping '${PROJECT_VERSION}' to '${NEXT_VERSION}'"
	@sed -i -e s/"version=\".*\""/"version=\"${NEXT_VERSION}\""/g setup.py
	@sed -i -e s/"^VERSION_PATCH = .*"/"VERSION_PATCH = ${NEXT_VERSION_PATCH}"/g modules/cij/__init__.py

.PHONY: clean
clean:
	@rm -r build || true
	@rm -r dist || true

.PHONY: release-build
release-build:
	python setup.py sdist
	python setup.py bdist_wheel

.PHONY: release-upload
release-upload:
	twine upload dist/*

.PHONY: release
release: clean release-build release-upload
	@echo -n "# rel: "; date

.PHONY: selftest
selftest:
	@rm -r selftest_results || true
	./selftest.sh 0 selftest_results

.PHONY: selftest-view
selftest-view:
	@rm -r selftest_results || true
	./selftest.sh 1 selftest_results

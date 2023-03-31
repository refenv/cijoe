#
# This Makefile serves as convenient command-line auto-completion
#
PROJECT_NAME=cijoe
PYTEST=~/.local/pipx/venvs/cijoe/bin/pytest
PYTHON=python3
PIPX=pipx
TWINE=twine

define default-help
# invoke: 'make uninstall', 'make install'
endef
.PHONY: default
default: build
	@echo "## py: make default"
	@echo "## py: make default [DONE]"

define  all-help
# Do all: clean uninstall build install
endef
.PHONY: all
all: uninstall clean build install test

define build-help
# Build the package (source distribution package)
endef
.PHONY: build
build:
	@echo "## py: make build-sdist"
	@${PYTHON} setup.py sdist
	@echo "## py: make build-sdist [DONE]"

define install-help
# install for current user
endef
.PHONY: install
install:
	@echo "## py: make install"
	@${PIPX} install dist/*.tar.gz
	@echo "## py: make install [DONE]"

define uninstall-help
# uninstall
#
# Prefix with 'sudo' when uninstalling a system-wide installation
endef
.PHONY: uninstall
uninstall:
	@echo "## py: make uninstall"
	@${PIPX} uninstall ${PROJECT_NAME} || echo "Cannot uninstall => That is OK"
	@echo "## py: make uninstall [DONE]"

define examples-help
# Run pytest on the testcase-test
endef
.PHONY: test
test:
	@echo "## py: make test"
	${PYTEST} --pyargs cijoe.core.selftest --config src/cijoe/core/configs/default.config
	@echo "## py: make test [DONE]"

.PHONY: release-build
release-build:
	${PYTHON} setup.py sdist
	${PYTHON} setup.py bdist_wheel

.PHONY: release-upload
release-upload:
	${TWINE} upload dist/*

.PHONY: release
release: clean release-build release-upload
	@echo -n "# rel: "; date

define clean-help
# clean the Python build dirs (build, dist)
endef
.PHONY: clean
clean:
	@echo "## py: clean"
	@git clean -fdx || echo "Failed git-clean ==> That is OK"
	@echo "## py: clean [DONE]"

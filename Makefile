#
# This Makefile serves as convenient command-line auto-completion
#
PROJECT_NAME=cijoe
BUILD=pyproject-build
PIPX=pipx
PYTEST="$(shell pipx environment -V PIPX_LOCAL_VENVS)/${PROJECT_NAME}/bin/pytest"
PYTHON_SYS=python3
PYTHON_VENV="$(shell pipx environment -V PIPX_LOCAL_VENVS)/${PROJECT_NAME}/bin/python3"
TWINE=twine
CIJOE_VERSION=$(shell cd src; python3 -c "from cijoe import core;print(core.__version__)")

define default-help
# invoke: 'make uninstall', 'make install'
endef
.PHONY: default
default: build
	@echo "## ${PROJECT_NAME}: make default"
	@echo "## ${PROJECT_NAME}: make default [DONE]"

define  all-help
# Do all: clean uninstall build install
endef
.PHONY: all
all: uninstall clean deps build install info test

define deps-help
# Dependencies for building cijoe and uploading it to PyPI
endef
.PHONY: deps
deps:
	${PIPX} install build || true
	${PIPX} install twine || true

define info-help
# Dump various Python / tooling information
endef
.PHONY: info
info:
	@echo "## ${PROJECT_NAME}: make info"
	${BUILD} --version || true
	${PIPX} --version || true
	${PYTEST} --version || true
	${PYTHON_SYS} --version || true
	${PYTHON_VENV} --version || true
	${TWINE} --version || true
	@echo "## ${PROJECT_NAME}: make info [DONE]"

define docker-help
# drop into a docker instance with the repository bind-mounted at /tmp/source
endef
.PHONY: docker
docker:
	@echo "## ${PROJECT_NAME}: docker"
	@docker run -it \
				-w /tmp/source \
				--mount type=bind,source="$(shell pwd)",target=/tmp/source \
				ghcr.io/refenv/cijoe-docker \
				bash
	@echo "## ${PROJECT_NAME}: docker [DONE]"


define docker-build-help
# Build docker image
endef
.PHONY: docker-build
docker-build:
	@echo "## ${PROJECT_NAME}: docker"
	@docker buildx build \
		--build-arg CIJOE_VERSION=${CIJOE_VERSION} \
		--tag ghcr.io/refenv/cijoe-docker:latest \
		--file .github/cijoe-docker/Dockerfile \
		.
	@echo "## ${PROJECT_NAME}: docker [DONE]"



define docker-privileged-help
# drop into a privileged docker instance with the repository bind-mounted at /tmp/source
endef
.PHONY: docker-privileged
docker-privileged:
	@echo "## ${PROJECT_NAME}: docker"
	@docker run -it \
				--privileged \
				-w /tmp/source \
				--mount type=bind,source="$(shell pwd)",target=/tmp/source \
				ghcr.io/refenv/cijoe-docker \
				bash
	@echo "## ${PROJECT_NAME}: docker [DONE]"

define format-help
# run code format (style, code-conventions and language-integrity) on staged changes
endef
.PHONY: format
format:
	@echo "## ${PROJECT_NAME}: format"
	@pre-commit run
	@echo "## ${PROJECT_NAME}: format [DONE]"

define format-all-help
# run code format (style, code-conventions and language-integrity) on staged and committed changes
endef
.PHONY: format-all
format-all:
	@echo "## ${PROJECT_NAME}: format-all"
	@pre-commit run --all-files
	@echo "## ${PROJECT_NAME}: format-all [DONE]"

define build-help
# Build the package (sdist and wheel using sdist)
endef
.PHONY: build
build:
	@echo "## ${PROJECT_NAME}: make build"
	@${BUILD}
	@echo "## ${PROJECT_NAME}: make build [DONE]"

define install-help
# install for current user
endef
.PHONY: install
install:
	@echo "## ${PROJECT_NAME}: make install"
	@${PIPX} install dist/*.tar.gz --include-deps --force --python python3
	@${PIPX} inject cijoe coverage --include-apps --force
	@echo "## ${PROJECT_NAME}: make install [DONE]"

define uninstall-help
# uninstall
#
# Prefix with 'sudo' when uninstalling a system-wide installation
endef
.PHONY: uninstall
uninstall:
	@echo "## ${PROJECT_NAME}: make uninstall"
	@${PIPX} uninstall ${PROJECT_NAME} || echo "Cannot uninstall => That is OK"
	@echo "## ${PROJECT_NAME}: make uninstall [DONE]"

define examples-help
# Run pytest on the testcase-test
endef
.PHONY: test
test:
	@echo "## ${PROJECT_NAME}: make test"
	${PYTEST} --pyargs cijoe.core.selftest --config src/cijoe/core/configs/example_config_default.toml -v -s
	@echo "## ${PROJECT_NAME}: make test [DONE]"

define examples-help
# Run pytest on the testcase-test
endef
.PHONY: release
release: all
	@echo "## ${PROJECT_NAME}: make release"
	@echo -n "# rel: "; date
	@${TWINE} upload dist/*
	@echo "## ${PROJECT_NAME}: make release"

define clean-help
# clean the Python build dirs (build, dist)
endef
.PHONY: clean
clean:
	@echo "## ${PROJECT_NAME}: clean"
	@git clean -fdx || echo "Failed git-clean ==> That is OK"
	@echo "## ${PROJECT_NAME}: clean [DONE]"

PY_BIN ?= python3
PY_ENV_PATH = venv
PY_ENV_ACTIVATE = . ${PY_ENV_PATH}/bin/activate
PY_ENV = ${PY_ENV_ACTIVATE} && ${PY_BIN}

SPHINX_SOURCEDIR=source
SPHINX_BUILDDIR=build

all: venv-setup clean kmdo build view
#all: venv-setup clean apidoc kmdo build view

define build-help
# Remove auto-generated documentation the source-dir and the generated docs in build-dir
endef
.PHONY: clean
clean:
	@echo "## clean"
	rm -rf "${SPHINX_BUILDDIR}"
	rm -rf "${SPHINX_SOURCEDIR}/api"

define apidoc-help
# Generate api documentation using Sphinx autodoc
endef
.PHONY: apidoc
apidoc:
	@echo "## apidoc"
	${PY_ENV_ACTIVATE} && sphinx-apidoc --implicit-namespaces -e -H "API" -M -f --tocfile index -o ${SPHINX_SOURCEDIR}/api ../src/cijoe

define kmdo-help
# Generate api documentation using Sphinx autodoc
endef
.PHONY: kmdo
kmdo:
	@echo "## kmdo"
	kmdo source

define build-help
# Build the documentation (invoke sphinx)
endef
.PHONY: build
build:
	@echo "## build"
	${PY_ENV_ACTIVATE} && sphinx-build -b html ${SPHINX_SOURCEDIR} ${SPHINX_BUILDDIR}

define build-help
# Open the HTML documentation using (xdg-open)
endef
.PHONY: view
view:
	@echo "## open docs"
	xdg-open "${SPHINX_BUILDDIR}/index.html"

define build-py-env-help
# Setup a virtual environment
endef
.PHONY: venv-setup
venv-setup:
	@echo "## venv-setup(${PY_ENV_PATH})"
	@${PY_BIN} -m venv ${PY_ENV_PATH}
	@echo "## venv-setup: upgrading pip"
	@${PY_ENV} -m pip install --upgrade pip
	@echo "## venv-setup: installing dependencies (for sphinx)"
	@${PY_ENV} -m pip install -r requirements.txt
	@echo "## venv-setup: installing cijoe (for sphinx autodoc)"
	@${PY_ENV} -m pip install ..
	@${PY_ENV} -m pip install ../../cijoe-pkg-qemu
	@${PY_ENV} -m pip install ../../cijoe-pkg-linux
	@${PY_ENV} -m pip install ../../cijoe-pkg-fio

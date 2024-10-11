SPHINX_SOURCEDIR=source
SPHINX_BUILDDIR=build
PYTHON=$(shell pipx environment --value PIPX_LOCAL_VENVS)/cijoe/bin/python

all: venv-setup clean build view

define build-help
# Remove auto-generated documentation the source-dir and the generated docs in build-dir
endef
.PHONY: clean
clean:
	@echo "## clean"
	rm -rf "${SPHINX_BUILDDIR}"
	rm -rf "${SPHINX_SOURCEDIR}/api"

.PHONY: emit-section-packages
emit-section-packages:
	@echo "## section:packages"
	${PYTHON} ./emit.py

define apidoc-help
# Generate api documentation using Sphinx autodoc
endef
.PHONY: apidoc
apidoc:
	@echo "## apidoc"
	sphinx-apidoc --implicit-namespaces -e -H "API" -M -f --tocfile index -o ${SPHINX_SOURCEDIR}/api ../src/cijoe

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
	sphinx-build -b html ${SPHINX_SOURCEDIR} ${SPHINX_BUILDDIR}

define build-help
# Open the HTML documentation
endef
.PHONY: view
view:
	@echo "## open docs"
	xdg-open "${SPHINX_BUILDDIR}/index.html" || open "${SPHINX_BUILDDIR}/index.html"

define build-py-env-help
# Setup a virtual environment using pipx
endef
.PHONY: venv-setup
venv-setup:
	pipx install ../dist/cijoe-*.tar.gz --force --include-deps
	xargs -a requirements.txt -I {} pipx inject cijoe {} --force --include-deps

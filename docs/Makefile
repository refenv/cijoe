SPHINX_SOURCEDIR=source
SPHINX_BUILDDIR=build
PYTHON='$(shell pipx environment --value PIPX_LOCAL_VENVS)/cijoe/bin/python'

.PHONY: common
common: clean build view

.PHONY: all
all: venv-setup kmdo clean build view

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
	@rm -rf "${SPHINX_SOURCEDIR}/packages/"
	${PYTHON} ./emit.py

.PHONY: docker-build
docker-build:
	docker build -t cijoe-docgen .

.PHONY: docker
docker: docker-build
	docker run -it --rm \
		-v $(shell pwd)/../:/cijoe \
		--user $(shell id -u):$(shell id -g) \
		cijoe-docgen \
		bash -c "cd /cijoe && make all && cd docs && make all"

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

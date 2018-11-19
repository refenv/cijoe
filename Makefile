PROJECT_NAME=cijoe
PROJECT_VERSION_MAJOR=$(shell grep "VERSION_MAJOR = ." modules/cij/__init__.py | cut -d " " -f 3)
PROJECT_VERSION_MINOR=$(shell grep "VERSION_MINOR = ." modules/cij/__init__.py | cut -d " " -f 3)
PROJECT_VERSION_PATCH=$(shell grep "VERSION_PATCH = ." modules/cij/__init__.py | cut -d " " -f 3)
PROJECT_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}
NEXT_VERSION_PATCH=$$((${PROJECT_VERSION_PATCH} + 1))
NEXT_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${NEXT_VERSION_PATCH}

.PHONY: install
install:
	pip install .

.PHONY: uninstall
uninstall:
	pip uninstall ${PROJECT_NAME} || true

.PHONY: dev
dev: uninstall install
	echo "# Yup"

.PHONY: bump
bump:
	@echo "# Bumping '${PROJECT_VERSION}' to '${NEXT_VERSION}'"
	@sed -i -e s/"^VERSION_PATCH = .*"/"VERSION_PATCH = ${NEXT_VERSION_PATCH}"/g modules/cij/__init__.py
	@sed -i -e s/"version=\".*\""/"version=\"${NEXT_VERSION}\""/g setup.py

.PHONY: release-build
release-build:
	python setup.py sdist
	python setup.py bdist_wheel

.PHONY: release-upload
release-upload:
	twine upload dist/*

.PHONY: release
release: release-build release-upload
	@echo "# DONE"

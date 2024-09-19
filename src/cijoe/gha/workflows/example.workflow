---
doc: |
  GitHub Action Runner

steps:
- name: build
  uses: gha.runner_download

- name: install
  uses: gha.runner_setup

- name: uninstall
  uses: gha.runner_remove

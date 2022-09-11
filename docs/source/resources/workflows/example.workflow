---
doc: |
  This is a workflow file, it serves as an example on how to run commands and worklets, the
  structure intentionally mimics that of GitHUB actions, however, the keys you see here are all
  there is.

  Running commands, as you can see below, looks just like running commands in a GitHUB Workflow

  * Add the 'run' key with a value of multi-line string

  Using worklets, it is similar to that of a GitHUB action

  * Add the 'uses' key with the name of the worklet
    - packaged worklets have a namespaced name e.g. "my_pkg.my_worklet"
    - non-packaged do not e.g. "my_worklet"
  * Add the 'with' key providing arguments to the worklet

  The commands and the worklets are passed an instance of cijoe which they can use to call
  run()/get()/put(), with an output-directory matching the current step. This is it, end of story.

steps:
- name: info
  run: |
    cat /proc/cpuinfo
    hostname

- name: test
  uses: core.testrunner
  with:
    args: "--pyargs cijoe.core.selftest"

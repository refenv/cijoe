# Hooks

Hooks are scripts/executables that the `cij_runner` can execute as `ENTER` or
`EXIT`. That is, before and after something happens. Specifically:

 * As `cij_runner` starts executing (`ENTER`) and as it stops executing (`EXIT`)
 * Before (`ENTER`) and after(`EXIT`) `cij_runner` executes a testsuite
 * Before (`ENTER`) and after(`EXIT`) `cij_runner` executes a testcase

Expressed in pseudo-Python code, then hooks execute like this:

```python
def cij_runner():

	for hook in hook_trun_enter:
		hook_run(...)

	for tsuite in testsuites:
		for hook in hook_tsuite_enter:
			hook_run(...)

		for tcase in testcases:
			hook_tcase_enter(...)

			RUN_TCASE(...)

			hook_tcase_exit(...)

		for hook in hook_tsuite_exit:
			hook_run(...)

	for hook in hook_trun_exit:
		hook_run(...)
```

A hook can have scripts named like this:

```bash
	lnvm_enter.sh
	lnvm_exit.sh
```

When it does, then the name of the hook is `lnvm`, and it has two different
scripts to run, depending of if it used as `enter` or as `exit`.

If it only has a name like:

```bash
	sysinf.sh
```

Then the name of hook is `sysinf` and it will only run as an `ENTER` hook.

## Implementing Hooks

Have a look at the existing hooks, they are currently equivalent to testcases.
However, this will be refactored in the future with `test::hook_enter` methods,
and `hook::enter`, `hook::require`, etc. methods. For now they can behave as
small tests but in the future this will probably make a lot of clutter, so
expect this to change.

## cij_runner

One instructs the `cij_runner` to use a hook at the different points by defining
the usage in a testplan (.plan) file.

# Test Suites

Each file ending with `.suite` in this directory is a test suite definition.
The `.suite` file must contain a subset of the files in the `$CIJ_TESTCASES`
directory.

See `$CIJ_TESTPLANS` for documentation on how testsuites are used.

The absolute path to this directory is defined as environment variable:

```bash
CIJ_TESTSUITES=$CIJ_PKG_ROOT/testsuites
```


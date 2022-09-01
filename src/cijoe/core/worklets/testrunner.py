"""
testrunner
==========

Invokes 'pytest' for cijoe testcases

It is intended for a specific use of pytest with the plugins listed below, it is as
such not a completely open-ended pytest-invocation as the cijoe-testcases must utilize
'cijoe.run' etc. to encapsulate command-execution, capture command output, and
collector artifacts.

Requires the following pytest plugins for correct behaviour:

 * cijoe, fixtures providing 'cijoe' object and "--config" and "--output"
 pytest-arguments to instantiate cijoe.

 * report-log, dump testnode-status as JSON, this is consumed by 'core.report' to
 produce an overview of testcases and link them with the cijoe-captured output and
 auxilary files.

Retargetable: False
-------------------

Although the worklet is not retargetable, then the pytest-plugin itself is retargetable.
"""


def worklet_entry(args, cijoe, step):
    """Invoke test-runner"""

    pytest_cmd = ["python3", "-m", "pytest"]
    pytest_cmd += ["--output", str(args.output / cijoe.output_ident)]
    pytest_cmd += [
        "--report-log",
        str(args.output / cijoe.output_ident / "testreport.log"),
    ]

    if args.config:
        pytest_cmd.append("--config")
        pytest_cmd.append(str(args.config))

    pytest_cmd += step.get("with").get("args", "").split(" ")

    err, _ = cijoe.run_local(" ".join(pytest_cmd))

    return err

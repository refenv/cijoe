#!/usr/bin/env python
"""
    Example of a testcase implemented as a Python script

    The test implementation itself just verifies whether it can execute a
    command without error, it is just a demonstration on how commands should be
    invoked and how test-status must be communicated
"""
import cij.test
import cij.ssh
import cij
cij.test.enter()

def main():
    """
    @returns cij.test.PASS on success and cij.test.FAIL otherwise
    """

    cmd = ["lspci"]
    rcode, _, _ = cij.ssh.command(cmd, shell=True, echo=False)

    return cij.test.FAIL if rcode else cij.test.PASS

if __name__ == "__main__":
    cij.test.texit(rcode=main())

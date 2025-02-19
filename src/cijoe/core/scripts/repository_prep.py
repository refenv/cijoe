"""
repository_prep
===============

For every key in the configuration which has a subkey named "repository", then
following is done:

 * git clone repository.remote                   # if ! exists(repository.path)
 * git checkout [repository.branch,repository.tag] # if repository.{branch,tag}
 * git pull --rebase                               # if repository.branch
 * git status

The intended usage of this script is to prepare a repositories in a recently
provisioned system. Such as a done by 'qemu.provision'.

Configuration
-------------

Ensure that the "repository" has sensible values for:

* remote: url of the repository to clone

* branch: name of the branch to check out and rebase
* tag: name of the tag to check out

* run_local: Optionally, set 'run_local' to True, in case the repos should just be
  checked out locally, instead of on the remote.

Retargetable: True
------------------
"""

import errno
import logging as log
from pathlib import Path


def main(args, cijoe):
    """Clone, checkout branch and pull"""

    err, _ = cijoe.run("git --version")
    if err:
        log.error("Looks like git is not available")
        return err

    for repos in [
        r["repository"] for r in cijoe.config.options.values() if "repository" in r
    ]:
        run = cijoe.run_local if repos.get("run_local", False) else cijoe.run

        repos_root = Path(repos["path"]).parent

        err, _ = run(f"mkdir -p {repos_root}")
        if err:
            log.error("failed creating repos_root({repos_root}; giving up")
            return err

        err, _ = run(
            f"[ ! -d {repos['path']} ] &&"
            f" git clone {repos['remote']} {repos['path']} --recursive"
        )
        if err:
            log.info("either already cloned or failed cloning; continuing optimisticly")

        err, _ = run("git fetch --all", cwd=repos["path"])
        if err:
            log.info("fetching failed; continuing optimisticly")

        do_checkout = repos.get("branch", repos.get("tag", None))
        if do_checkout:
            err, _ = run(f"git checkout {do_checkout}", cwd=repos["path"])
            if err:
                log.error("Failed checking out; giving up")
                return err
        else:
            log.info("no 'branch' nor 'tag' key; skipping checkout")

        if "branch" in repos.keys():
            err, _ = run("git pull --rebase", cwd=repos["path"])
            if err:
                log.error("failed pulling; giving up")
                return err

        err, _ = run("git submodule update --init --recursive", cwd=repos["path"])
        if err:
            log.info("Updating submodules failed; continuin optimisticly")

        err, _ = run("git status", cwd=repos["path"])
        if err:
            log.error("failed 'git status'; giving up")
            return err

    return 0

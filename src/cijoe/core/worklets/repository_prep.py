"""
repository_prep
===============

For every key in the configuration which has a subkey named "repository", then
following is done:

 * git clone repository.upstream                   # if ! exists(repository.path)
 * git checkout [repository.branch,repository.tag] # if repository.{branch,tag}
 * git pull --rebase                               # if repository.branch
 * git status

The intended usage of this worklet is to prepare a repositories in a recently
provisioned system. Such as a done by 'qemu.provision'.

Configuration
-------------

Ensure that the "repository" has sensible values for:
* {upstream,path,branch}"

Retargetable: True
------------------
"""
import errno
import logging as log
from pathlib import Path


def worklet_entry(args, cijoe, step):
    """Clone, checkout branch and pull"""

    err, _ = cijoe.run("git --version")
    if err:
        log.err("Looks like git is not available")
        return err

    for repos in [
        r["repository"] for r in cijoe.config.options.values() if "repository" in r
    ]:
        if len(set(["upstream", "path"]) - set(repos.keys())):
            continue
        if "qemu" in repos["upstream"]:
            continue

        repos_root = Path(repos["path"]).parent

        err, _ = cijoe.run(f"mkdir -p {repos_root}")
        if err:
            log.error("failed creating repos_root({repos_root}; giving up")
            return err

        err, _ = cijoe.run(
            f"[ ! -d {repos['path']} ] &&"
            f" git clone {repos['upstream']} {repos['path']} --recursive"
        )
        if err:
            log.info("either already cloned or failed cloning; continuing optimisticly")

        do_checkout = repos.get("branch", repos.get("tag", None))
        if do_checkout:
            err, _ = cijoe.run(f"git checkout {do_checkout}", cwd=repos["path"])
            if err:
                log.error("Failed checking out; giving up")
                return err
        else:
            log.info("no 'branch' nor 'tag' key; skipping checkout")

        if "branch" in repos.keys():
            err, _ = cijoe.run("git pull --rebase", cwd=repos["path"])
            if err:
                log.error("failed pulling; giving up")
                return err

        err, _ = cijoe.run("git status", cwd=repos["path"])
        if err:
            log.error("failed 'git status'; giving up")
            return err

    return 0

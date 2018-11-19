# Testplans

The absolute path to this directory is defined as environment variable:

```bash
CIJ_TESTPLANS=$CIJ_PKG_ROOT/testplans
```

## Usage example

Execute testplan `testplan_demo01.sh` in environment `ch-twinja01.sh`.

```bash
$CIJ_TESTPLANS/testplan_demo01.sh $CIJ_ENVS/ch-twinja01.sh | tee plan.log
```

This will create a file `plan.log` and output info similar to:

```bash
# CIJ_PLAN_NAME: 'testplan_demo01.sh'
# CIJ_PLAN_ROOT: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N'
# TESTPLAN: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N', {'/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo', 'foo'}
# rnr::ENVIRONMENT VARIABLES {
#               CIJ_ENVS: '/home/safl/git/cijoe/envs'
#              CIJ_HOOKS: '/home/safl/git/cijoe/hooks'
#            CIJ_MODULES: '/home/safl/git/cijoe/modules'
#               CIJ_ROOT: '/home/safl/git/cijoe'
#          CIJ_TESTCASES: '/home/safl/git/cijoe/testcases'
#         CIJ_TESTSUITES: '/home/safl/git/cijoe/testsuites'
#          CIJ_TEST_HOST: None
#      CIJ_TEST_RES_ROOT: None
# }
# rnr::COMMAND-LINE ARGUMENTS {
#                env: '/home/safl/git/cijoe/envs/ch-twinja01.sh'
#          env_fname: 'ch-twinja01.sh'
#          env_fpath: '/home/safl/git/cijoe/envs/ch-twinja01.sh'
#           env_name: 'ch-twinja01'
#      hook_pr_tcase: None
#       hook_pr_trun: ['dmesg', 'sysinf']
#     hook_pr_tsuite: None
#             output: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo'
#          testsuite: ['/home/safl/git/cijoe/testsuites/demo01.suite']
#    testsuite_fpath: ['/home/safl/git/cijoe/testsuites/demo01.suite']
#            verbose: 2
# }
# rnr::HOOKS {
#      tcase: {'exit': [], 'enter': []}
#       trun: {'exit': ['/home/safl/git/cijoe/hooks/dmesg_exit.sh'], 'enter': ['/home/safl/git/cijoe/hooks/dmesg_enter.sh', '/home/safl/git/cijoe/hooks/sysinf.sh']}
#     tsuite: {'exit': [], 'enter': []}
# }
# rnr::INFO {
#   output: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo'
#   yml_fpath: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/trun.yml'
# }
# rnr::hook:run: { hook_fpath: '/home/safl/git/cijoe/hooks/dmesg_enter.sh' }
# rnr::hook:run: { hook_log_path: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/run.log' }
# rnr::hook:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo" source /home/safl/git/cijoe/hooks/dmesg_enter.sh ' }
# rnr::hook:run: PASS { rcode: 0 } 
# rnr::hook:run: { hook_fpath: '/home/safl/git/cijoe/hooks/sysinf.sh' }
# rnr::hook:run: { hook_log_path: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/run.log' }
# rnr::hook:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo" source /home/safl/git/cijoe/hooks/sysinf.sh ' }
# rnr::hook:run: PASS { rcode: 0 } 
# rnr::tsuite:enter { name: 'demo01' }
# 
# rnr::tcase:enter: { fname: 'pci_enum.sh' }
# rnr::tcase:enter: { log_fpath: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/demo01/pci_enum.sh/run.log' }
# rnr::tcase:enter: { cur: 1 }
# rnr::tcase:run: { fname: 'pci_enum.sh' }
# rnr::tcase:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/demo01/pci_enum.sh" source /home/safl/git/cijoe/testcases/pci_enum.sh' }
# rnr::tcase:run: { wallc: 1.580938 }
# rnr::tcase:run: { rcode: 0 }
# rnr::tcase:run: { status: PASS, rcode: 0 }
# 
# rnr::tcase:enter: { fname: 'nvme_enum_linux.sh' }
# rnr::tcase:enter: { log_fpath: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/demo01/nvme_enum_linux.sh/run.log' }
# rnr::tcase:enter: { cur: 2 }
# rnr::tcase:run: { fname: 'nvme_enum_linux.sh' }
# rnr::tcase:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/demo01/nvme_enum_linux.sh" source /home/safl/git/cijoe/testcases/nvme_enum_linux.sh' }
# rnr::tcase:run: { wallc: 2.176927 }
# rnr::tcase:run: { rcode: 1 }
# rnr::tcase:run: { status: FAIL, rcode: 1 }
# rnr::hook:run: { hook_fpath: '/home/safl/git/cijoe/hooks/dmesg_exit.sh' }
# rnr::hook:run: { hook_log_path: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo/run.log' }
# rnr::hook:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo" source /home/safl/git/cijoe/hooks/dmesg_exit.sh ' }
# rnr::hook:run: PASS { rcode: 0 } 
# rnr::main: { output: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-foo' }
# rnr::main: { progress: {'count': 2, 'failed': 1, 'current': 2, 'passed': 1} }
# FAIL
# running PLAN: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N', {'/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar', 'bar'}
# rnr::ENVIRONMENT VARIABLES {
#               CIJ_ENVS: '/home/safl/git/cijoe/envs'
#              CIJ_HOOKS: '/home/safl/git/cijoe/hooks'
#            CIJ_MODULES: '/home/safl/git/cijoe/modules'
#               CIJ_ROOT: '/home/safl/git/cijoe'
#          CIJ_TESTCASES: '/home/safl/git/cijoe/testcases'
#         CIJ_TESTSUITES: '/home/safl/git/cijoe/testsuites'
#          CIJ_TEST_HOST: None
#      CIJ_TEST_RES_ROOT: None
# }
# rnr::COMMAND-LINE ARGUMENTS {
#                env: '/home/safl/git/cijoe/envs/ch-twinja01.sh'
#          env_fname: 'ch-twinja01.sh'
#          env_fpath: '/home/safl/git/cijoe/envs/ch-twinja01.sh'
#           env_name: 'ch-twinja01'
#      hook_pr_tcase: None
#       hook_pr_trun: ['dmesg', 'sysinf']
#     hook_pr_tsuite: None
#             output: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar'
#          testsuite: ['/home/safl/git/cijoe/testsuites/demo02.suite']
#    testsuite_fpath: ['/home/safl/git/cijoe/testsuites/demo02.suite']
#            verbose: 2
# }
# rnr::HOOKS {
#      tcase: {'exit': [], 'enter': []}
#       trun: {'exit': ['/home/safl/git/cijoe/hooks/dmesg_exit.sh'], 'enter': ['/home/safl/git/cijoe/hooks/dmesg_enter.sh', '/home/safl/git/cijoe/hooks/sysinf.sh']}
#     tsuite: {'exit': [], 'enter': []}
# }
# rnr::INFO {
#   output: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar'
#   yml_fpath: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/trun.yml'
# }
# rnr::hook:run: { hook_fpath: '/home/safl/git/cijoe/hooks/dmesg_enter.sh' }
# rnr::hook:run: { hook_log_path: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/run.log' }
# rnr::hook:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar" source /home/safl/git/cijoe/hooks/dmesg_enter.sh ' }
# rnr::hook:run: PASS { rcode: 0 } 
# rnr::hook:run: { hook_fpath: '/home/safl/git/cijoe/hooks/sysinf.sh' }
# rnr::hook:run: { hook_log_path: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/run.log' }
# rnr::hook:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar" source /home/safl/git/cijoe/hooks/sysinf.sh ' }
# rnr::hook:run: PASS { rcode: 0 } 
# rnr::tsuite:enter { name: 'demo02' }
# 
# rnr::tcase:enter: { fname: 'pci_enum.sh' }
# rnr::tcase:enter: { log_fpath: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/demo02/pci_enum.sh/run.log' }
# rnr::tcase:enter: { cur: 1 }
# rnr::tcase:run: { fname: 'pci_enum.sh' }
# rnr::tcase:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/demo02/pci_enum.sh" source /home/safl/git/cijoe/testcases/pci_enum.sh' }
# rnr::tcase:run: { wallc: 1.543028 }
# rnr::tcase:run: { rcode: 0 }
# rnr::tcase:run: { status: PASS, rcode: 0 }
# 
# rnr::tcase:enter: { fname: 'nvme_enum_linux.sh' }
# rnr::tcase:enter: { log_fpath: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/demo02/nvme_enum_linux.sh/run.log' }
# rnr::tcase:enter: { cur: 2 }
# rnr::tcase:run: { fname: 'nvme_enum_linux.sh' }
# rnr::tcase:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/demo02/nvme_enum_linux.sh" source /home/safl/git/cijoe/testcases/nvme_enum_linux.sh' }
# rnr::tcase:run: { wallc: 2.116050 }
# rnr::tcase:run: { rcode: 1 }
# rnr::tcase:run: { status: FAIL, rcode: 1 }
# rnr::hook:run: { hook_fpath: '/home/safl/git/cijoe/hooks/dmesg_exit.sh' }
# rnr::hook:run: { hook_log_path: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar/run.log' }
# rnr::hook:run: { cmd: 'bash -c source cijoe.sh && source /home/safl/git/cijoe/envs/ch-twinja01.sh && CIJ_TEST_RES_ROOT="/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar" source /home/safl/git/cijoe/hooks/dmesg_exit.sh ' }
# rnr::hook:run: PASS { rcode: 0 } 
# rnr::main: { output: '/tmp/tplan-testplan_demo01.sh-L5VFAV0N/trun-bar' }
# rnr::main: { progress: {'count': 2, 'failed': 1, 'current': 2, 'passed': 1} }
# FAIL
```

Testsuites are run by executing `cij_runner`:

```bash
usage: cij_runner [-h] --testplan TESTPLAN --env ENV [--output OUTPUT] [-v]

cij_runner - CIJOE Test Runner

optional arguments:
  -h, --help           show this help message and exit
  --testplan TESTPLAN  Path to the testplan to run (default: None)
  --env ENV            Path to the environment definition (default: None)
  --output OUTPUT      Path to directory in which to store runner output
                       (default: /tmp/trun-f8b18596)
  -v, --verbose        increase output verbosity, 0 = quiet, 1 = some, 1 >
                       alot (default: 0)
```

## Testrun example

Run the testplan `EXAMPLE01.plan` in the `ch-twinja04` environment:

```bash
cij_runner \
--testplan $CIJ_TESTPLANS/TPLAN-example-01.plan \
--env $CIJ_ENVS/ch-lab-dragon.sh
```

The above command will execute the testplan as defined by `EXAMPLE01.plan` in the
environment `ch-twinja04.sh`.

NOTE: Add `-v` to increase verbosity of the runner.

NOTE: The first thing `cij_runner` informs you about is where output from the
testrun is stored. You can also provide `--output` if you wish to store results
in a specific location.

# Test Reports

After, or during, the execution of `cij_runner` a test report can be generated
by running the following:

```bash
cij_reporter --output /tmp/trun -v
```

You can optionally add the param `--template` with a path to another template
than the default.

## Prerequisites

The `environment` must be setup, configured and defined in `$CIJ_ROOT`, see XX
for detailed information on deploying environments.

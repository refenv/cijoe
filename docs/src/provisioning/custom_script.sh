#!/usr/bin/env bash
#
# Template workflow/provision script using CIJOE
#
SCRIPT=$(basename $0)
PROJECT="foobar"
pushd $(cij_root) && source modules/cijoe.sh && popd

task_build() {
  cij.info "Bulding!"
}

task_deploy() {
  cij.info "Deploying!"
}

task_run() {
  cij.info "Running! E.g. invoking cij_runner..."
}

task_postprocess() {
  cij.info "Postprogressing! E.g. invoking cij_reporter, etc."
  cij.info "Invoke other tools for post-processing the testrun"
}

task_all() {
  task_build $@
  task_deploy $@
  task_run $@
  task_postprocess $@
}

task_help() {
  echo "Usage: ${SCRIPT} <command> <env>"
  echo "Commands:"
  echo "  build <env>           ; Build ${PROJECT} in <env> or for deployment to <env>"
  echo "  deploy <env>          ; Deploy ${PROJECT} to <env>"
  echo "  run <env>             ; Invoke test-runner for ${PROJECT} in <env>"
  echo "  postprocess <env>     ; Postprocess results from 'run'"
  echo "  all <env>             ; Do all the tasks above in/to/for <env>"
}

main() {
  task=$1
  env=$2

  case $task in
  "" | "-h" | "--help")
    task_help
    ;;
  *)
    shift

    if [[ ! -f "$env" ]]; then
      cij.err "Invalid env: '$env'"
      task_help
      exit 1
    fi

    source "$env"
    task_${task} $@
    if [ $? = 127 ]; then
        echo "Error: '$task' is not a known task." >&2
        echo " Run '${SCRIPT} --help' for a list of known tasks." >&2
        exit 1
    fi
    ;;
  esac
}

main $@

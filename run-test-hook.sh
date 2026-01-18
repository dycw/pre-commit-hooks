#!/usr/bin/env bash

# add hook to `project.scripts` and `.pre-commit-hooks.yaml`
# edit `HOOK_NAME` below
# in your project, run:
#     ~/work/pre-commit-hooks/run-test-hook.sh

PATH_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit
	pwd -P
)"
HOOK_NAME='add-hooks'

pre-commit try-repo --verbose --all-files "${PATH_DIR}" "${HOOK_NAME}"

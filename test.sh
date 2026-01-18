#!/usr/bin/env bash

# in your project, run:
#     ~/personal/pre-commit-hooks/run-test-hook.sh

if [ "$#" -ne 1 ]; then
	echo "'run-test-hook.sh' expects exactly 1 argument; got $#"
	exit 1
fi

PATH_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit
	pwd -P
)"
HOOK=$1
prek try-repo --all-files --show-diff-on-failure --fail-fast --verbose "${PATH_DIR}" "${HOOK}"

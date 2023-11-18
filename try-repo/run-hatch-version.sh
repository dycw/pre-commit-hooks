#!/usr/bin/env bash

PATH_SCRIPTS_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit
	pwd -P
)"
PATH_REPO_ROOT="$(dirname "${PATH_SCRIPTS_DIR}")"

echo "$PATH_SCRIPTS_DIR"
echo "$PATH_REPO_ROOT"
pre-commit try-repo --all-files "$PATH_REPO_ROOT" run-hatch-version "$@"

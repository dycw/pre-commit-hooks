#!/usr/bin/env bash

# usage: edit the following in `.pre-commit-hooks.yaml`
#
# - id: test-hook
#   name: test-hook
#   entry: run-uv-pip-compile
#   language: python
#   files: ^pyproject\.toml$
#   pass_filenames: false
#   description: Run `uv pip compile`
#   args: [
#       --output-file=requirements-macos.txt
#       --extra=interactive
#       --python-platform=macos
#       --python-version=3.12,
#     ]
#
# then, in your project, run:
#
# ❯ ../pre-commit-hooks/run-test-hook.sh

PATH_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit
	pwd -P
)"

pre-commit try-repo --verbose --all-files "$PATH_DIR" test-hook

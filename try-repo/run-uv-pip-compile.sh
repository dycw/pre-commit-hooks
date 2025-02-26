#!/usr/bin/env bash

CALLER_DIR="$(readlink -f .)"
pre-commit try-repo --verbose --all-files "$CALLER_DIR" run-uv-pip-compile "$@"

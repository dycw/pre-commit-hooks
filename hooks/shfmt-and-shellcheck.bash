#!/usr/bin/env bash

if [ "$#" -eq 1 ]; then
  root=$(git rev-parse --show-toplevel)
  file=$(realpath --relative-to="$root" "$1")

	printf "shfmt -> %s...\n" "$file"
	shfmt -w "$1"
	shfmt_code=$?
	if [ $shfmt_code -eq 0 ]; then
		printf "shellcheck -> %s...\n" "$file"
		shellcheck "$1"
		shellcheck_code="$?"
		exit $shellcheck_code
	else
		exit $?
	fi
else
	here="$(readlink -f "$0")"
	printf "%s expects exactly 1 parameter; got %s\n" "$here" "$#"
	exit 1
fi

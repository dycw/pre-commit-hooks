#!/usr/bin/env bash
# here="$(dirname "$(readlink -f "$0")")"

if [ "$#" -eq 1 ]; then
	printf "Running shmft on %s...\n" "$1"
	shfmt -w "$1"
	shfmt_code=$?
	printf "shfmt returned %s\n" "$shfmt_code"
	if [ $shfmt_code -eq 0 ]; then
		printf "Running shellcheck on %s...\n" "$1"
		shellcheck "$1"
		shellcheck_code="$?"
		printf "shellcheck returned \n%s" "$shellcheck_code"
		exit $shellcheck_code
	else
		printf "shfmt returnd %s\n" "$shfmt_code"
		exit $shfmt_code
	fi
else
	here="$(readlink -f "$0")"
	printf "%s expects exactly 1 parameter; got %s\n" "$here" "$#"
	exit 1
fi

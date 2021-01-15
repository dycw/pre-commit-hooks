#!/usr/bin/env bash

if [ "$#" -eq 1 ]; then
	root=$(git rev-parse --show-toplevel)
	desc=$(realpath --relative-to="$root" "$1")

	printf "shfmt -> %s\n" "$desc"
	shfmt -w "$1"
	shfmt_code=$?
	if [ $shfmt_code -eq 0 ]; then
		git add "$1"
		printf "shellcheck -> %s\n" "$desc"
		shellcheck "$1"
	fi
	echo "Returning..........$?"
	exit $?
else
	here="$(readlink -f "$0")"
	printf "%s expects exactly 1 parameter; got %s\n" "$here" "$#"
	exit 1
fi

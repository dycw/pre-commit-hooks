#!/usr/bin/env bash

needs_run() {
	if [[ "$1" == *.bash ]]; then
		return 0
	fi
	line=$(head -n 1 "$1")
	if [[ "$line" == *bash* ]]; then
		return 0 # this is untested
	else
		return 1
	fi
}

run_hook() {
	if ! needs_run "$1"; then
		return 0
	fi

	root=$(git rev-parse --show-toplevel)
	desc=$(realpath --relative-to="$root" "$1")
	printf "Running shfmt > %s\n" "$desc"
	if ! shfmt -w "$1"; then
		return 1
	fi
	git add "$1"
	printf "Running shellcheck > %s\n" "$desc"
	shellcheck "$1"
	return $?
}

if run_hook "$1"; then
	exit 0
else
	exit 1
fi

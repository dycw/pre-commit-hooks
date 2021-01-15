#!/usr/bin/env bash

needs_run() {
	if [[ "$1" == *.bash ]]; then
		return 0
	fi

	line=$(head -n 1 "$1")
	if [[ "$line" == *bash* ]]; then
		return 0
	else
		return 1
	fi
}

run_hook() {
	if ! shfmt -w "$1"; then
		return 1
	fi
	git add "$1"
	shellcheck "$1"
	return $?
}

if needs_run "$1" && run_hook "$1"; then
	exit 0
else
	exit 1
fi

#!/usr/bin/env bash

needs_run() {
	if [[ "$1" == *.bash ]]; then
		return 0
	fi

	line=$(head -n 1 "$1")
	if [[ "$line" == *bash* ]]; then
		return 0
	else
		if [ -n "$PRE_COMMIT_DEBUG" ]; then
			printf "Skipping shfmt and shellcheck on %s\n" "$1"
		fi
		return 1
	fi
}

run_hook() {
	if [ -n "$PRE_COMMIT_DEBUG" ]; then
		printf "Running shfmt on %s\n" "$1"
	fi
	if ! shfmt -w "$1"; then
		return 1
	fi

	git add "$1"

	if [ -n "$PRE_COMMIT_DEBUG" ]; then
		printf "Running shellcheck on %s\n" "$1"
	fi

	shellcheck "$1"
	return $?
}

if needs_run "$1" && run_hook "$1"; then
	exit 0
else
	exit 1
fi

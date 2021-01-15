#!/usr/bin/env bash

if [ "$#" -eq 1 ]; then
	path="$1"
	if [ -f "$path" ]; then
		root=$(git rev-parse --show-toplevel)
		desc=$(realpath --relative-to="$root" "$1")

		printf "shfmt -> %s\n" "$desc"
		shfmt -w "$path"
		shfmt_code=$?
		if [ $shfmt_code -eq 0 ]; then
			git add "$path"
			printf "shellcheck -> %s\n" "$desc"
			shellcheck "$path"
			exit $?
		else
			exit $shfmt_code
		fi
	elif [ -d "$path" ]; then
		while read -r file; do
			printf "We are gonna run shfmt-and-shellcheck on %s\n" "$file"
		done <<<"$(git ls-files "$path")"
	fi
else
	here="$(readlink -f "$0")"
	printf "%s expects exactly 1 parameter; got %s\n" "$here" "$#"
	exit 1
fi

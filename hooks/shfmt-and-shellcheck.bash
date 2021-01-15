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
		code=0
		while read -r file; do
			if ! shfmt-and-shellcheck "$file"; then
				code=1
			fi
		done <<<"$(git ls-files "$path")"
		exit $code
	fi
else
	here="$(readlink -f "$0")"
	printf "%s expects exactly 1 parameter; got %s\n" "$here" "$#"
	exit 1
fi

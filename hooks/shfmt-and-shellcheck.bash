#!/usr/bin/env bash

check_is_file() {
	echo "Checking if $1 is a bash file"
	if [ -f "$1" ]; then
		if [[ "$1" == *.bash ]]; then
			line=$(head -n 1 "$1")
			if [[ "$line" == *bash* ]]; then
				exit 0
			else
				exit 1
			fi
		else
			exit 0
		fi
	else
		exit 1
	fi
}

if [ "$#" -eq 1 ]; then
	is_file=$(check_is_file "$1")
	if [ "$is_file" -eq 0 ]; then
		root=$(git rev-parse --show-toplevel)
		desc=$(realpath --relative-to="$root" "$1")
		printf "shfmt -> %s\n" "$desc"
		shfmt -w "$1"
		shfmt_code=$?
		if [ $shfmt_code -eq 0 ]; then
			git add "$1"
			printf "shellcheck -> %s\n" "$desc"
			shellcheck "$1"
			exit $?
		else
			exit $shfmt_code
		fi
	elif [ -d "$1" ]; then
		code=0
		while read -r file; do
			if ! shfmt-and-shellcheck "$file"; then
				code=1
			fi
		done <<<"$(git ls-files "$1")"
		exit $code
	else
		exit 0
	fi
else
	printf "Expected exactly 1 parameter; got %s\n" "$#"
	exit 1
fi

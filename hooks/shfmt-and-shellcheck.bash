#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
	printf "Expected exactly 1 parameter; got %s\n" "$#"
	exit 1
fi

check_is_file() {
	echo "$1 here"
	if ! [   -f "$1" ]; then
			exit 1
	fi
	echo "$1 here2"
	if [ "$1" == "*.bash" ]; then
			echo "$1"
		exit 0
	fi
			line=$(head -n 1 "$1")
			if [[ "$line" == *bash* ]]; then
				exit 0
			else
				exit 1
			fi
}


if check_is_file "$1";   then

		root=$(git rev-parse --show-toplevel)
		desc=$(realpath --relative-to="$root" "$1")
		echo trying shfmt "$1"
		if ! shfmt -w "$1"; then
			exit 1
		fi
		git add "$1"
		if shellcheck "$1"; then
		exit 0
		else
		exit 1
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
fi

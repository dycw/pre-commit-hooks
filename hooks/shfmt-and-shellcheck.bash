#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
	printf "Expected exactly 1 parameter; got %s\n" "$#"
	exit 1
fi

maybe_process_file() {
	echo "$1 here"
	if [ "$1" == "*.bash" ]; then
		echo "$1"
	exit 0
	fi
	line=$(head -n 1 "$1")
	if [[ "$line" != *bash* ]]; then
			exit 1
	fi

	# have a bash file now
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
}


if [ -f "$1 "];   then
	maybe_process_file "$1"
	elif [ -d "$1" ]; then
		failed=0
		while read -r file; do
			if ! maybe_process_file "$file"; then
				failed=1
			fi
		done <<<"$(git ls-files "$1")"
		if [  $failed -eq 0 ]
		then
		exit 0
		else
		exit 1
		fi
	else
		exit 0
	fi
fi

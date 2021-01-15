#!/usr/bin/env bash

to_check() {
	if [ "$1" == "*.bash" ]; then
		return 0
	fi
	line=$(head -n 1 "$1")
	if [[ "$line" == *bash* ]]; then
		return 0 # this is untested
	else
		return 1
	fi
}

handle_file() {
	if ! to_check "$1"; then
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
	if shellcheck "$1"; then
		return 0
	else
		return 1
	fi
}

handle_path() {
	if [ -f "$1" ]; then
		if handle_file "$1"; then
			return 0
		else
			return 1
		fi
	elif [ -d "$1" ]; then
		failed=0
		while read -r file; do
			if handle_file "$file"; then
				failed=1
			fi
		done <<<"$(git ls-files "$1")"
		if [ $failed -eq 0 ]; then
			return 0
		else
			return 1
		fi
	else
		return 0
	fi
}

if handle_path "$1"; then
	exit 0
else
	exit 1
fi

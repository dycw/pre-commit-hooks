#!/usr/bin/env bash

handle_file() {
	echo "$1 here"
	if [ "$1" == "*.bash" ]; then
		echo "$1"
		return 0
	fi
	line=$(head -n 1 "$1")
	if [[ "$line" != *bash* ]]; then
		return 1 # this is untested
	fi

	# have a bash file now
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

handle_path() {
	if [ -f "$1" ]; then
		handle_file "$1"
		return $?
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

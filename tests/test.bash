#!/usr/bin/env bash

while read -r file; do
	printf "We got file\n%s\n" "$file"
	root=$(git rev-parse --show-toplevel)
	full="$root/$file"
	if [ -f "$full" ]; then
		echo 'exists'
	else
		echo 'no'

	fi
done <<<"$(git diff --name-only --cached)"

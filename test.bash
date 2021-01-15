#!/usr/bin/env bash

a="123"
if [ "$a" -eq 1 ]; then
	echo "$a"
fi

declare -a files
while read -r file; do
	if [ -n "$file" ]; then
		files+=("$file")
	fi
done <<<"$(git diff --name-only --cached)"
if [ ${#files[@]} -eq 0 ]; then
	printf "No files found at this stage\n"
else
	printf "Yes files found at this stage\n"
fi

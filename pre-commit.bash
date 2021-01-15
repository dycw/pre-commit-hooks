#!/usr/bin/env bash
# shellcheck source=/dev/null

root=$(git rev-parse --show-toplevel)
code=0
while read -r file; do
	if [ -n "$file" ]; then
		full_file="$root/$file"
		while read -r hook; do
			if ! "$hook" "$full_file"; then
				code=1
			fi
		done <<<"$(find "$root/hooks" -type f)"
	fi
done <<<"$(git diff --name-only --cached)"

if [ $code -eq 0 ]; then
	declare -a post_files
	while read -r file; do
		if [ -n "$file" ]; then
			post_files+=("$file")
		fi
	done <<<"$(git diff --name-only --cached)"
	if [ ${#post_files[@]} -eq 0 ]; then
		exit 1
	else
		exit 0
	fi
else
	exit $code
fi

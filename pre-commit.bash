#!/usr/bin/env bash
# shellcheck source=/dev/null

declare -a pre_files
while read -r file; do
	if [ -n "$file" ]; then
		pre_files+=("$file")
	fi
done <<<"$(git diff --name-only --cached)"

root=$(git rev-parse --show-toplevel)
hooks_dir="$root/hooks"

declare -a hooks
while read -r hook; do
	hooks+=("$hook")
done <<<"$(find "$hooks_dir" -type f)"

if [ ${#hooks[@]} -eq 0 ]; then
	printf "No hooks found; please check %s\n" "$hooks_dir"
	exit 1
fi

code=0
for file in "${pre_files[@]}"; do
	full_file="$root/$file"
	for hook in "${hooks[@]}"; do
		(. "$hook" "$full_file")
		if [ $# -ne 0 ]; then
			code=1
		fi
	done
	# git add "$full_file"
done

if [ $code -ne 0 ]; then
	exit $code
fi

declare -a post_files
while read -r file; do
	if [ -n "$file" ]; then
		post_files+=("$file")
	fi
done <<<"$(git diff --name-only --cached)"
if [ ${#post_files[@]} -eq 0 ]; then
	exit 0
fi

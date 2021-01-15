#!/usr/bin/env bash
# shellcheck source=/dev/null

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

declare -a files
while read -r file; do
	if [ -n "$file" ]; then
		files+=("$file")
	fi
done <<<"$(git diff --name-only --cached)"

if [ ${#files[@]} -eq 0 ]; then
	printf "No files found\n"
	exit 0
else
	printf "Files found\n"
	for file in "${files[@]}"; do
		printf "We have files to: %s\n" "$file"
	done

fi

code=0
for hook in "${hooks[@]}"; do
	for file in "${files[@]}"; do
		full_file="$root/$file"
		if ! . "$hook" "$full_file"; then
			code=1
		fi
	done
done

if [ $code -eq 0 ]; then
	foo=$(git diff --cached --exit-code)
	echo "foo=$foo"
	# git status --untracked-files=no --porcelain
fi

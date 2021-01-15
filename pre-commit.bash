#!/usr/bin/env bash
# shellcheck source=/dev/null

declare -a files
while read -r file; do
	if [ -n "$file" ]; then
		files+=("$file")
	fi
done <<<"$(git diff --name-only --cached)"

root=$(git rev-parse --show-toplevel)
hooks_dir="$root/hooks"

declare -a hooks
while read -r hook; do
	hooks+=("$hook")
done <<<"$(find "$hooks_dir" -type f)"

# if [ ${#hooks[@]} -eq 0 ]; then
# 	printf "No hooks found; please check %s\n" "$hooks_dir"
# 	exit 1
# fi

code=0
for file in "${files[@]}"; do
	full_file="$root/$file"
	for hook in "${hooks[@]}"; do
		if ! . "$hook" "$full_file"; then
			code=1
		fi
	done
	# git add "$full_file"
done

echo got this point with code "$code"

if [ $code -ne 0 ]; then
	exit $code
	# git status --untracked-files=no --porcelain
fi

echo got 2nd point

declare -a files2
while read -r file2; do
	if [ -n "$file2" ]; then
		files2+=("$file2")
	fi
done <<<"$(git diff --name-only --cached)"
if [ ${#files2[@]} -eq 0 ]; then
	printf "No files found at this stage\n"
	exit 1
else
	printf "At the end, did find %s files\n" ${#files2[@]}
fi

#!/usr/bin/env bash
# shellcheck source=/dev/null

root=$(git rev-parse --show-toplevel)

declare -a hooks
while read -r hook; do
	hooks+=("$hook")
done <<<"$(find "$root"/hooks -type f)"

declare -a files
while read -r file; do
	files+=("$file")
done <<<"$(git diff --name-only --cached)"

code=0
for hook in "${hooks[@]}"; do
	for file in "${files[@]}"; do
		full_file="$root/$file"
		if ! . "$hook" "$full_file"; then
			code=1
		fi
	done
done

exit $code

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
	# hook_name=$(basename "$hook")
	for file in "${files[@]}"; do
		full_file="$root/$file"
		(
			set -e
			source "$hook" "$full_file"
		)
		# inner_code=$?
		# if [ $inner_code -eq 0 ]; then
		# 	echo "OK with $hook_name on $file"

		# else
		# 	echo "Failed with $hook_name on $file"
		# 	code=1
		# fi

		inner_code=$?
		if [ $inner_code -ne 0 ]; then
			code=1
		fi
	done
done

if [ $code -eq 0 ]; then
	exit 0
else
	exit 1
fi

exit $code

#!/usr/bin/env bash

files=$(git diff --name-only --cached)
declare -a theArray
while read -r line; do
	theArray+=("$line")
done <<<"$files"

root=$(git rev-parse --show-toplevel)

declare -a hooks
while read -r hook; do
	hooks+=("$hook")
done <<<"$(find "$root"/hooks -type f)"

for hook in "${hooks[@]}"; do
	echo then...
	echo "hook=$hook"
done

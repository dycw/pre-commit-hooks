#!/usr/bin/env bash

declare -a files
while read -r line; do
	if ! [ -z "$line"]
	then
	echo "Adding '$line'..."
	files+=("$line")
	fi
done <<<$(git diff --name-only --cached)

for file in "${files[@]}"; do
	echo then...
	echo "file=$file"
done

if [ ${#files[@]} -eq 0 ]; then
    echo "No files"
else
    echo "Yes files"
fi
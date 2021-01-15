#!/usr/bin/env bash
# shellcheck source=/dev/null

handle_path() {
	path="$1"
	hook="$2"
	if [ -f "$path" ]; then
		"$hook" "$path"
		return $?
	elif [ -d "$path" ]; then
		code=0
		while read -r file; do
			if ! handle_path "$file" "$hook"; then
				code=1
			fi
		done <<<"$(git ls-files "$path")"
		return $code
	else
		return 0
	fi
}

run-hooks() {
	root=$(git rev-parse --show-toplevel)
	code=0
	while read -r path; do
		while read -r hook; do
			if ! handle_path "$root/$file" "$hook"; then
				code=1
			fi
		done <<<"$(find "$root/hooks" -type f)"
	done <<<"$(git diff --name-only --cached)"
	return $code
}

check-git-status() {
	if [ -z "$(git status --untracked-files=no --porcelain)" ]; then
		return 1
	else
		return 0
	fi
}

if run-hooks && check-git-status; then
	exit 0
else
	exit 1
fi

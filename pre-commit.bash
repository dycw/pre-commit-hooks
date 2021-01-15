#!/usr/bin/env bash
# shellcheck source=/dev/null

run_hooks_on_file_path() {
	root=$(git rev-parse --show-toplevel)
	code=0
	while read -r hook; do
		if ! "$hook" "$1"; then
			code=1
		fi
	done <<<"$(find "$root/hooks" -type f)"
	return $code
}

run_hooks_on_all_files() {
	root=$(git rev-parse --show-toplevel)
	code=0
	while read -r staged_file; do
		path_staged="$root/$staged_file"
		if [ -f "$path_staged" ]; then
			run_hooks_on_file_path "$path_staged"
			return $?
		elif [ -d "$path_staged" ]; then
			code=0
			while read -r file_staged; do
				if ! run_hooks_on_file_path "$root/$file_staged"; then
					code=1
				fi
			done <<<"$(git ls-files "$path_staged")"
			return $code
		else
			return 0
		fi
	done <<<"$(git diff --name-only --cached)"
	return $code
}

check_git_status() {
	if [ -z "$(git status --untracked-files=no --porcelain)" ]; then
		return 1
	else
		return 0
	fi
}

if run_hooks_on_all_files && check_git_status; then
	exit 0
else
	exit 1
fi

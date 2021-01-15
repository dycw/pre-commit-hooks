#!/usr/bin/env bash
# shellcheck source=/dev/null

run_hooks_on_file() {
	root=$(git rev-parse --show-toplevel)
	code=0
	while read -r hook; do
		if ! "$hook" "$root/$file"; then
			code=1
		fi
	done <<<"$(find "$root/hooks" -type f)"
	return $code
}

run_hooks_on_all_files() {
	root=$(git rev-parse --show-toplevel)
	code=0
	while read -r path; do
		if [ -f "$path" ]; then
			run_hooks_on_file "$path"
			return $?
		elif [ -d "$path" ]; then
			code=0
			while read -r file; do
				if ! run_hooks_on_file "$file"; then
					code=1
				fi
			done <<<"$(git ls-files "$path")"
			return        $code
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

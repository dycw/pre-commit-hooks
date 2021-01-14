#!/usr/bin/env bash
root=$(dirname "$(readlink -f "$0")")
target=$root/.git/hooks/pre-commit

if [ -f "$target" ]; then
	printf "Uninstalling pre-commit hooks from:\n    %s\n" "$target"
	rm "$target"
else
	printf "No pre-commit hooks are currently installed at:\n    %s\n" "$target"
fi

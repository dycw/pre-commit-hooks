#!/usr/bin/env bash
root=$(git rev-parse --show-toplevel)
# root=$(dirname "$(readlink -f "$0")")
target=$root/.git/hooks/pre-commit

if [ -f "$target" ]; then
	printf "Pre-commit hooks are already installed at:\n    %s\n" "$target"
	echo For now we overwrite...
	source="$root/pre-commit.bash"
	./uninstall.bash
	cp "$source" "$target"
else
	printf "Installing pre-commit hooks at:\n    %s\n" "$target"
	source="$root/pre-commit.bash"
	cp "$source" "$target"
fi

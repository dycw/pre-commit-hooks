#!/usr/bin/env sh

here=$(readlink -f "$0")
here=$(dirname "$here")
link_name="$here/.git/hooks/pre-commit"

if [ -f "$link_name" ]; then
	echo "$link_name already exists"
else
	echo "Creating $link_name..."
	target="$here/pre-commit.sh"
	ln -s "$target" "$link_name"
fi

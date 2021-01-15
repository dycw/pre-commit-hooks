#!/usr/bin/env bash

echo anotherline >>foo
echo anotherline >>bar
./install.bash

shfmt -w "$path"
shfmt_code=$?
if [$shfmt_code -eq 0 ]; then
	git add "$path"
	printf "shellcheck -> %s\n" "$desc"
	shellcheck "$path"
	exit $?
else
	exit $shfmt_code
fi

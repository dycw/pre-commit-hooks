#!/usr/bin/env sh


a=1234
b="$a"
root=$(git rev-parse --show-toplevel)
path="$root/.git/hooks/pre-commit"
echo $root
rm "$root"
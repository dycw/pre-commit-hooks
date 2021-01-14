#!/usr/bin/env sh


a=1234
b="$a"

mypath=$(exec 2>/dev/null;cd -- $(dirname "$0"); unset PWD; /usr/bin/pwd || /bin/pwd || pwd)
echo mypath="$mypath"
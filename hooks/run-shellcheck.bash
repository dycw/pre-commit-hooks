#!/usr/bin/env bash
# here="$(dirname "$(readlink -f "$0")")"



if [ "$#" -eq 1 ]
then
    echo "I'm gonna shellcheck "$1""
    exit 0
else
  here="$(readlink -f "$0")"
  echo "Expected exactly 1 parameter; got $#"
    exit 1
fi



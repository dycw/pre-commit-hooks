#!/usr/bin/env bash
# here="$(dirname "$(readlink -f "$0")")"



if [ "$#" -eq 1 ]
then
    echo "Running shmft on "$1"..."
    shfmt -d "$1"
    error_code=$?
		echo "shfmt returned $error_code"
    exit 0
else
  here="$(readlink -f "$0")"
  echo "Expected exactly 1 parameter; got $#"
    exit 1
fi



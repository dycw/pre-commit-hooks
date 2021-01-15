#!/usr/bin/env bash
# here="$(dirname "$(readlink -f "$0")")"



if [ "$#" -eq 1 ]
then
    printf "Running shmft on %s..." "$1"
    shfmt -w "$1"
    shfmt_code=$?
		printf "shfmt returned %s" "$shfmt_code"
    if [ $shfmt_code -eq 0 ]; then
      printf "Running shellcheck on %s..." "$1"
      shellcheck "$1"
      shellcheck_code="$?"
      printf "shellcheck returned $shellcheck_code"
      return shellcheck_code
		else



			printf "shfmt returnd $shfmt_code"
      return $shfmt
		fi

else
  here="$(readlink -f "$0")"
  printf "%s expects exactly 1 parameter; got $#"
    exit 1
fi



#!/usr/bin/env bash
# here="$(dirname "$(readlink -f "$0")")"
here="$(readlink -f "$0")"
echo Running "$here"


if [ "$#" -eq 1 ]
then

  echo "ok"
  exit 1
else
    echo "Illegal number of parameters"
    exit 1
fi


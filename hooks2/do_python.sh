#!/usr/bin/env bash

format_file() {
	# black
	if ! command -v black >/dev/null 2>&1; then
		printf "ERROR: black missing\n"
		return 1
	fi
	if ! black --quiet "$1"; then
		printf "ERROR: black failed on %s\n" "$1"
		return 1
	fi

	# ## add-trailing-comma
	# if ! command -v add-trailing-comma >/dev/null 2>&1; then
	# 	printf "ERROR: add-trailing-comma missing\n"
	# 	return 1
	# fi
	# if ! add-trailing-comma --exit-zero-even-if-changed --py36-plus "$1"; then
	# 	printf "ERROR: add-trailing-comma failed on %s\n" "$1"
	# fi
	# if ! black --quiet "$1"; then
	# 	printf "ERROR: black (after add-trailing-comma) failed on %s\n" "$1"
	# 	return 1
	# fi

	# ## autoflake
	# if ! command -v autoflake >/dev/null 2>&1; then
	# 	printf "ERROR: autoflake missing\n"
	# 	return 1
	# fi
	# autoflake --in-place --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables "$1"
	# if ! black --quiet "$1"; then
	# 	printf "ERROR: black (after autoflake) failed on %s\n" "$1"
	# 	return 1
	# fi

	# ## pyupgrade
	# if ! command -v pyupgrade >/dev/null 2>&1; then
	# 	printf "ERROR: pyupgrade missing\n"
	# 	return 1
	# fi
	# if ! pyupgrade --exit-zero-even-if-changed --py38-plus "$1"; then
	# 	printf "ERROR: pyupgrade failed on %s\n" "$1"
	# fi
	# if ! black --quiet "$1"; then
	# 	printf "ERROR: black (after pyupgrade) failed on %s\n" "$1"
	# 	return 1
	# fi

	# ## reorder-python-imports
	# if ! command -v reorder-python-imports >/dev/null 2>&1; then
	# 	printf "ERROR: reorder-python-imports missing\n"
	# 	return 1
	# fi
	# if ! reorder-python-imports --exit-zero-even-if-changed --py38-plus "$1" >/dev/null 2>&1; then
	# 	printf "ERROR: reorder-python-imports failed on %s\n" "$1"
	# fi
	# if ! black --quiet "$1"; then
	# 	printf "ERROR: black (after reorder-python-imports) failed on %s\n" "$1"
	# 	return 1
	# fi

	# ## yesqa
	# if ! command -v yesqa >/dev/null 2>&1; then
	# 	printf "ERROR: yesqa missing\n"
	# 	return 1
	# fi
	# if ! yesqa "$1" >/dev/null 2>&1; then
	# 	printf "ERROR: yesqa failed on %s\n" "$1"
	# fi
	# if ! black --quiet "$1"; then
	# 	printf "ERROR: black (after yesqa) failed on %s\n" "$1"
	# 	return 1
	# fi

	# # fixers - end
	# git add "$1"

	# # linters
	# ## flake8
	# if ! command -v flake8 >/dev/null 2>&1; then
	# 	printf "ERROR: flake8 missing\n"
	# 	return 1
	# fi
	# python_dir="$(dirname "$(dirname "${BASH_SOURCE[0]}")")/python"
	# if ! flake8 --config="$python_dir/.flake8" "$1"; then
	# 	printf "ERROR: flake8 failed on %s\n" "$1"
	# 	return 1
	# fi

	# ## mypy
	# if ! command -v mypy >/dev/null 2>&1; then
	# 	printf "ERROR: mypy missing\n"
	# 	return 1
	# fi
	# if ! mypy --config="$python_dir/mypy.ini" "$1"; then
	# 	printf "ERROR: mypy failed on %s\n" "$1"
	# 	return 1
	# fi

	# # linters - end
	return 0
}

for file in "$@"; do
	format_file "./$(dirname "$file")"
done

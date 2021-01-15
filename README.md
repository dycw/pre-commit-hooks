# pre-commit-hooks

## Overview

`git` pre-commit hooks written in `bash`.

## Installation

Add the repo to yours as a submodule using:

```bash
git submodule add -b master git@github.com:dycw/pre-commit-hooks.git .pre-commit-hooks
./.pre-commit-hooks/install
```




## Debugging

If you need to see which hooks are run and/or skipped, set the following environment variable:

```bash
export PRE_COMMIT_DEBUG=1
```

## Updating

Update the submodule and re-install the pre-commit script as follows:

```bash
git submodule update --init --recursive --remote -- .pre-commit-hooks
./.pre-commit-hooks/install --yes

```

# pre-commit-hooks

## Overview

`git` pre-commit hooks written in `bash`.

## Installation

Add this repository to yours using `git submodule`:

```bash
cd "$(git rev-parse --show-toplevel)" || return
git submodule add git@github.com:dycw/pre-commit-hooks.git .pre-commit-hooks
.pre-commit-hooks/install
```

## Debugging

If you need to see which hooks are run and/or skipped, set the following environment variable:

```bash
export PRE_COMMIT_DEBUG=1
```

## Updating

Run the following script:

```bash
"./$(git rev-parse --show-toplevel)/.pre-commit-hooks/update"
```




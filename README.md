# shell-pre-commit-hooks

## Installation

Add this repository as a git submodule to yours:

```bash
# git submodule add git@github.com:dycw/shell-pre-commit-hooks.git
cd $(git rev-parse --show-toplevel)
git submodule add git@github.com:dycw/shell-pre-commit-hooks.git .pre-commit-hooks
.pre-commit-hooks/install
```

As usual, updates can be fetched via:

```bash
git submodule foreach git pull origin master
```

## Debugging

If you need to see which hooks are run and/or skipped, set the following environment variable:

```bash
export PRE_COMMIT_DEBUG=1
```



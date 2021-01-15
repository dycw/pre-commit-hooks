# shell-pre-commit-hooks

## Depedencies

`git` and `bash`.

## Installation

Add this repository to yours using `git submodule`:

```bash
cd $(git rev-parse --show-toplevel)
git submodule add git@github.com:dycw/pre-commit-hooks.git .pre-commit-hooks
.pre-commit-hooks/install
```

## Debugging

If you need to see which hooks are run and/or skipped, set the following environment variable:

```bash
export PRE_COMMIT_DEBUG=1
```

## Updating

Update the submodule via `git submodule` and then re-install the pre-commit script:

```bash
git submodule foreach git pull origin master
$(git rev-parse --show-toplevel)/.pre-commit-hooks/install --yes
```

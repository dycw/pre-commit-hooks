# shell-pre-commit-hooks

## Installation

Add this repository to yours using `git submodule`:

```bash
# git submodule add git@github.com:dycw/shell-pre-commit-hooks.git
cd $(git rev-parse --show-toplevel)
git submodule add git@github.com:dycw/shell-pre-commit-hooks.git .pre-commit-hooks
.pre-commit-hooks/install
```

As usual, updates can be fetched via `git submodule`. For good measure, re-install the pre-commit script too:

```bash
git submodule foreach git pull origin master
$(git rev-parse --show-toplevel)/.pre-commit-hooks/install --overwrite
```

## Debugging

If you need to see which hooks are run and/or skipped, set the following environment variable:

```bash
export PRE_COMMIT_DEBUG=1
```



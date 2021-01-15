# shell-pre-commit-hooks

## Installation

```bash
# git submodule add git@github.com:dycw/shell-pre-commit-hooks.git
target="$(git rev-parse --show-toplevel)/.pre-commit-hooks"
git submodule add git@github.com:dycw/shell-pre-commit-hooks.git "$target"
"$target/install"
```

## Debugging

```bash
export PRE_COMMIT_DEBUG=1
```

to see which hooks are run and/or skipped.
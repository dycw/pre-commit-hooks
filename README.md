# shell-pre-commit-hooks

## Installation

```bash
# git submodule add git@github.com:dycw/shell-pre-commit-hooks.git
target="$(git rev-parse --show-toplevel)/.pre-commit-hooks"
git submodule add git@github.com:dycw/shell-pre-commit-hooks.git "$target"
"$target/install"
```


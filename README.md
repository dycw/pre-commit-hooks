# pre-commit-hooks

## Overview

My collection of [`pre-commit`](https://pre-commit.com/) hooks.

## Installation

1. Install `pre-commit`.
2. Add the following to your `.pre-commit-config.yaml`:

```bash
repos:
  - repo: https://github.com/dycw/pre-commit-hooks
    rev: master
    hooks:
      - id: elm
      - id: no-binary
      - id: no-commit
      - id: prettier
      - id: python
      - id: shell-exec
      - id: shell-non-exec
      - id: shellcheck
      - id: shfmt
      - id: text
      - id: universal
```

3. Update your `.pre-commit-config.yaml`:

```bash
pre-commit autoupdate
```

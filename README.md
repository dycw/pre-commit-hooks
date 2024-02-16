# pre-commit-hooks

## Overview

My [`pre-commit`](https://pre-commit.com/) hooks.

## Installation

1. Install `pre-commit`.

1. Add the following to your `.pre-commit-config.yaml`:

   ```yaml
   repos:
     - repo: https://github.com/dycw/pre-commit-hooks
       rev: master
       hooks:
         - id: run-bump2version
           args: [--setup-cfg]
         - id: run-dockfmt
         - id: run-hatch-version
         - id: run-ruff-format
         - id: run-uv-pip-compile
           args: [--python-version=3.9]
   ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

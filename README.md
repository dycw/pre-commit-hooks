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
         - id: run-dockfmt
         - id: run-poetry-export
         - id: run-scan-deps
   ```

   1. Additional arguments are supported:

      ```yaml
      - id: run-bump2version
        args: [--setup-cfg]
      ```

      or

      ```yaml
      - id: run-poetry-export
        args: [--filename=project/requirements.txt, --without-hashes, --dev]
      ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

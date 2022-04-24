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
         - id: bump-version
         - id: dockfmt
   ```

   This assumes you use `.bumpversion.cfg` to manage `bump2version`, i.e., for
   storing the version number. If you use `setup.cfg`, which `bump2version`,
   supply the extra argument:
   supports, then add:

   ```yaml
   - id: bump-version
     args: [--setup-cfg]
   ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

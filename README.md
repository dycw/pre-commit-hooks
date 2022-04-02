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
         - id: tag-commits-and-push-tags
   ```

   These assume you use `.bumpversion.cfg` to control `bump2version`, and
   store the version number. If you use `setup.cfg`, which `bump2version` also
   supports, then add:

   ```yaml
   - id: bump-version
     args: [--setup-cfg]
   - id: tag-commits-and-push-tags
     args: [--setup-cfg]
   ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

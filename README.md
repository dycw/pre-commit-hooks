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
         - id: check-submodules-updated
         - id: check-version-bumped
         - id: format-requirements
         - id: mirror-files
         - id: replace-sequence-str
         - id: run-bump-my-version
         - id: tag-commits
   ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

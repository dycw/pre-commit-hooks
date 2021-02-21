# pre-commit-hooks

## Overview

My collection of [`pre-commit`](https://pre-commit.com/) hook which ensures
consistency across projects. Inspired by [`nitpick`](https://github.com/andreoliwa/nitpick).

## Installation

1. Install `pre-commit`.
1. Add the following to your `.pre-commit-config.yaml`:

   ```bash
   repos:
     - repo: https://github.com/dycw/pre-commit-hooks
       rev: master
       hooks:
         - id: check-settings
   ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

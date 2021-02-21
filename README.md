# pre-commit-hooks

## Overview

My [`pre-commit`](https://pre-commit.com/) hook which ensures concistency
across my projects. Inspired by [`nitpick`](https://github.com/andreoliwa/nitpick).

Also exposes:

1. [`elm-format`](https://github.com/avh4/elm-format) (via `node`),
1. [`shfmt`](https://anaconda.org/conda-forge/go-shfmt) (via `conda`),

## Installation

1. Install `pre-commit`.
1. Add the following to your `.pre-commit-config.yaml`:

   ```bash
   repos:
     - repo: https://github.com/dycw/pre-commit-hooks
       rev: master
       hooks:
         - id: check-settings
         - id: elm-format
         - id: shfmt
   ```

1. Update your `.pre-commit-config.yaml`:

   ```bash
   pre-commit autoupdate
   ```

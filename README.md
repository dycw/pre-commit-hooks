# `pre-commit-hooks`

Pre-commit hooks

## Usage

In `.pre-commit-config.yaml`, add:

```yaml
repos:
  - repo: https://github.com/dycw/pre-commit-hooks
    rev: master
    hooks:
      - id: add-hooks
```

and then run `prek auto-update`.

from __future__ import annotations

from pre_commit_hooks.format_requirements import main

if __name__ == "__main__":
    raise SystemExit(int(not main()))

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest

from pre_commit_hooks.constants import (
    PYTHON_VERSION,
    RUFF_TOML,
    paths_argument,
    python_version_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    ensure_not_contains,
    get_set_array,
    get_set_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_version_option
def _main(*, paths: tuple[Path, ...], python_version: str | None = None) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=RUFF_TOML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, version=python_version) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = RUFF_TOML, version: str | None = None) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        version_use = PYTHON_VERSION if version is None else version
        doc["target-version"] = f"py{version_use.replace('.', '')}"
        doc["unsafe-fixes"] = True
        fmt = get_set_table(doc, "format")
        fmt["preview"] = True
        fmt["skip-magic-trailing-comma"] = True
        lint = get_set_table(doc, "lint")
        lint["explicit-preview-rules"] = True
        fixable = get_set_array(lint, "fixable")
        ensure_contains(fixable, "ALL")
        ignore = get_set_array(lint, "ignore")
        ensure_contains(
            ignore,
            "ANN401",  # any-type
            "ASYNC109",  # async-function-with-timeout
            "C901",  # complex-structure
            "CPY",  # flake8-copyright
            "D",  # pydocstyle
            "E501",  # line-too-long
            "PD",  # pandas-vet
            "PERF203",  # try-except-in-loop
            "PLC0415",  # import-outside-top-level
            "PLE1205",  # logging-too-many-args
            "PLR0904",  # too-many-public-methods
            "PLR0911",  # too-many-return-statements
            "PLR0912",  # too-many-branches
            "PLR0913",  # too-many-arguments
            "PLR0915",  # too-many-statements
            "PLR2004",  # magic-value-comparison
            "PT012",  # pytest-raises-with-multiple-statements
            "PT013",  # pytest-incorrect-pytest-import
            "PYI041",  # redundant-numeric-union
            "S202",  # tarfile-unsafe-members
            "S310",  # suspicious-url-open-usage
            "S311",  # suspicious-non-cryptographic-random-usage
            "S602",  # subprocess-popen-with-shell-equals-true
            "S603",  # subprocess-without-shell-equals-true
            "S607",  # start-process-with-partial-path
            # preview
            "S101",  # assert
            # formatter
            "W191",  # tab-indentation
            "E111",  # indentation-with-invalid-multiple
            "E114",  # indentation-with-invalid-multiple-comment
            "E117",  # over-indented
            "COM812",  # missing-trailing-comma
            "COM819",  # prohibited-trailing-comma
            "ISC001",  # single-line-implicit-string-concatenation
            "ISC002",  # multi-line-implicit-string-concatenation
        )
        lint["preview"] = True
        select = get_set_array(lint, "select")
        selected_rules = [
            "RUF022",  # unsorted-dunder-all
            "RUF029",  # unused-async
        ]
        ensure_contains(select, "ALL", *selected_rules)
        extend_per_file_ignores = get_set_table(lint, "extend-per-file-ignores")
        test_py = get_set_array(extend_per_file_ignores, "test_*.py")
        test_py_rules = [
            "S101",  # assert
            "SLF001",  # private-member-access
        ]
        ensure_contains(test_py, *test_py_rules)
        ensure_not_contains(ignore, *selected_rules, *test_py_rules)
        bugbear = get_set_table(lint, "flake8-bugbear")
        extend_immutable_calls = get_set_array(bugbear, "extend-immutable-calls")
        ensure_contains(extend_immutable_calls, "typing.cast")
        tidy_imports = get_set_table(lint, "flake8-tidy-imports")
        tidy_imports["ban-relative-imports"] = "all"
        isort = get_set_table(lint, "isort")
        req_imps = get_set_array(isort, "required-imports")
        ensure_contains(req_imps, "from __future__ import annotations")
        isort["split-on-trailing-comma"] = False
    return len(modifications) == 0


if __name__ == "__main__":
    _main()

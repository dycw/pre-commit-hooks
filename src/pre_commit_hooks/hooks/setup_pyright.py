from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest

from pre_commit_hooks.constants import (
    DEFAULT_PYTHON_VERSION,
    PYRIGHTCONFIG_JSON,
    RUFF_TOML,
    paths_argument,
    python_version_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_list_strs,
    run_all_maybe_raise,
    yield_json_dict,
)

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_version_option
def _main(
    *, paths: tuple[Path, ...], python_version: str = DEFAULT_PYTHON_VERSION
) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(
        *(
            partial(_run, path=p.parent / RUFF_TOML, python_version=python_version)
            for p in paths
        )
    )


def _run(
    *, path: PathLike = PYRIGHTCONFIG_JSON, python_version: str = DEFAULT_PYTHON_VERSION
) -> bool:
    modifications: set[Path] = set()
    with yield_json_dict(path, modifications=modifications) as dict_:
        dict_["deprecateTypingAliases"] = True
        dict_["enableReachabilityAnalysis"] = False
        include = get_set_list_strs(dict_, "include")
        ensure_contains(include, "src")
        dict_["pythonVersion"] = python_version
        dict_["reportCallInDefaultInitializer"] = True
        dict_["reportImplicitOverride"] = True
        dict_["reportImplicitStringConcatenation"] = True
        dict_["reportImportCycles"] = True
        dict_["reportMissingSuperCall"] = True
        dict_["reportMissingTypeArgument"] = False
        dict_["reportMissingTypeStubs"] = False
        dict_["reportPrivateImportUsage"] = False
        dict_["reportPrivateUsage"] = False
        dict_["reportPropertyTypeMismatch"] = True
        dict_["reportUninitializedInstanceVariable"] = True
        dict_["reportUnknownArgumentType"] = False
        dict_["reportUnknownMemberType"] = False
        dict_["reportUnknownParameterType"] = False
        dict_["reportUnknownVariableType"] = False
        dict_["reportUnnecessaryComparison"] = False
        dict_["reportUnnecessaryTypeIgnoreComment"] = True
        dict_["reportUnusedCallResult"] = True
        dict_["reportUnusedImport"] = False
        dict_["reportUnusedVariable"] = False
        dict_["typeCheckingMode"] = "strict"
    return len(modifications) == 0


if __name__ == "__main__":
    _main()

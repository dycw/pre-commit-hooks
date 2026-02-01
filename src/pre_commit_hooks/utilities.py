from __future__ import annotations

import json
from collections.abc import Iterator, MutableSet
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from functools import partial
from operator import eq
from pathlib import Path
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Any, overload

import tomlkit
import yaml
from libcst import Module, parse_module
from tomlkit import TOMLDocument, aot, array, document, string, table
from tomlkit.exceptions import ParseError
from tomlkit.items import AoT, Array, Table
from utilities.core import (
    OneEmptyError,
    ReadTextError,
    always_iterable,
    max_nullable,
    one,
    read_text,
    write_text,
)
from utilities.functions import ensure_class, ensure_str
from utilities.packaging import Requirement
from utilities.subprocess import RunError, run, uv_pip_list
from utilities.types import PathLike, StrDict
from utilities.typing import is_str_dict
from utilities.version import Version2, Version3, Version3Error

from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    PATH_CACHE,
    PRE_COMMIT_CONFIG_HOOK_KEYS,
    PRE_COMMIT_CONFIG_YAML,
    PRE_COMMIT_HOOKS_HOOK_KEYS,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, MutableSet

    from utilities.types import MaybeSequence, MaybeSequenceStr, PathLike, StrDict

    from pre_commit_hooks.types import (
        ArrayLike,
        ContainerLike,
        FuncRequirement,
        TransformArray,
        VersionSet,
    )


def add_modification(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> None:
    if modifications is not None:
        modifications.add(Path(path))


##


def add_update_certificates(steps: list[StrDict], /) -> None:
    ensure_contains(
        steps, {"name": "Update CA certificates", "run": "sudo update-ca-certificates"}
    )


##


def are_equal_modulo_new_line(x: str, y: str, /) -> bool:
    return ensure_new_line(x) == ensure_new_line(y)


##


@overload
def ensure_contains(container: AoT, /, *objs: Table) -> None: ...
@overload
def ensure_contains(container: list[str], /, *objs: str) -> None: ...
@overload
def ensure_contains(container: list[StrDict], /, *objs: StrDict) -> None: ...
def ensure_contains(container: ArrayLike, /, *objs: Any) -> None:
    for obj in objs:
        if obj not in container:
            container.append(obj)


def ensure_contains_partial_dict(
    container: list[StrDict], dict_: StrDict, /
) -> StrDict:
    try:
        return get_partial_dict(container, dict_)
    except OneEmptyError:
        container.append(dict_)
        return dict_


def ensure_contains_partial_str(list_: Array | list[str], text: str, /) -> str:
    try:
        return get_partial_str(list_, text)
    except OneEmptyError:
        list_.append(text)
        return text


@overload
def ensure_not_contains(container: AoT, /, *objs: Table) -> None: ...
@overload
def ensure_not_contains(container: list[str], /, *objs: str) -> None: ...
@overload
def ensure_not_contains(container: list[StrDict], /, *objs: StrDict) -> None: ...
def ensure_not_contains(container: ArrayLike, /, *objs: Any) -> None:
    for obj in objs:
        try:
            index = next(i for i, o in enumerate(container) if o == obj)
        except StopIteration:
            pass
        else:
            del container[index]


##


def ensure_new_line(text: str, /) -> str:
    return text.strip("\n") + "\n"


##


def get_aot(container: ContainerLike, key: str, /) -> AoT:
    return ensure_class(container[key], AoT)


def get_array(container: ContainerLike, key: str, /) -> Array:
    return ensure_class(container[key], Array)


def get_dict(dict_: StrDict, key: str, /) -> StrDict:
    if is_str_dict(value := dict_[key]):
        return value
    raise TypeError(value)


def get_list_dicts(dict_: StrDict, key: str, /) -> list[StrDict]:
    list_ = ensure_class(dict_[key], list)
    for i in list_:
        if not is_str_dict(i):
            raise TypeError(i)
    return list_


def get_list_strs(dict_: StrDict, key: str, /) -> list[str]:
    list_ = ensure_class(dict_[key], list)
    for i in list_:
        if not isinstance(i, str):
            raise TypeError(i)
    return list_


def get_table(container: ContainerLike, key: str, /) -> Table:
    return ensure_class(container[key], Table)


##


def get_partial_dict(dicts: list[StrDict], dict_: StrDict, /) -> StrDict:
    return one(i for i in dicts if _is_partial_dict(dict_, i))


def get_set_partial_dict(dicts: list[StrDict], dict_: StrDict, /) -> StrDict:
    try:
        return get_partial_dict(dicts, dict_)
    except OneEmptyError:
        copy = dict_.copy()
        dicts.append(copy)
        return copy


def _is_partial_dict(obj: Any, dict_: StrDict, /) -> bool:
    if not isinstance(obj, dict):
        return False
    results: dict[str, bool] = {}
    for key, obj_value in obj.items():
        try:
            dict_value = dict_[key]
        except KeyError:
            results[key] = False
        else:
            if isinstance(obj_value, dict) and isinstance(dict_value, dict):
                results[key] = _is_partial_dict(obj_value, dict_value)
            else:
                results[key] = obj_value == dict_value
    return all(results.values())


##


def get_partial_str(iterable: Iterable[Any], text: str, /) -> str:
    return one(i for i in iterable if _is_partial_str(i, text))


def _is_partial_str(obj: Any, text: str, /) -> bool:
    return isinstance(obj, str) and (text in obj)


##


def get_pyproject_dependencies(doc: TOMLDocument, /) -> PyProjectDependencies:
    out = PyProjectDependencies()
    try:
        project = get_table(doc, "project")
    except KeyError:
        pass
    else:
        with suppress(KeyError):
            out.dependencies = get_array(project, "dependencies")
        try:
            opt_dependencies = get_table(project, "optional-dependencies")
        except KeyError:
            pass
        else:
            out.opt_dependencies = {}
            for key in opt_dependencies:
                out.opt_dependencies[ensure_str(key)] = get_array(opt_dependencies, key)
    try:
        dep_grps = get_table(doc, "dependency-groups")
    except KeyError:
        pass
    else:
        out.dep_groups = {}
        for key in dep_grps:
            out.dep_groups[ensure_str(key)] = get_array(dep_grps, key)
    return out


@dataclass(kw_only=True, slots=True)
class PyProjectDependencies:
    dependencies: Array | None = None
    opt_dependencies: dict[str, Array] | None = None
    dep_groups: dict[str, Array] | None = None

    def map_array(self, func: TransformArray, /) -> None:
        if (deps := self.dependencies) is not None:
            func(deps)
        if (opt_depedencies := self.opt_dependencies) is not None:
            for deps in opt_depedencies.values():
                func(deps)
        if (dep_grps := self.dep_groups) is not None:
            for deps in dep_grps.values():
                func(deps)

    def map_requirements(self, func: FuncRequirement, /) -> None:
        if (deps := self.dependencies) is not None:
            self._map_requirements1(deps, func)
        if (opt_depedencies := self.opt_dependencies) is not None:
            for deps in opt_depedencies.values():
                self._map_requirements1(deps, func)
        if (dep_grps := self.dep_groups) is not None:
            for deps in dep_grps.values():
                self._map_requirements1(deps, func)

    def _map_requirements1(self, array: Array, func: FuncRequirement, /) -> None:
        new: list[str] = []
        for curr_i in array:
            req = Requirement(ensure_str(curr_i))
            new.append(str(func(req)))
        array.clear()
        for new_i in sorted(new):
            array.append(string(new_i))


##


def get_set_aot(container: ContainerLike, key: str, /) -> AoT:
    try:
        return get_aot(container, key)
    except KeyError:
        value = container[key] = aot()
        return value


def get_set_array(container: ContainerLike, key: str, /) -> Array:
    try:
        return get_array(container, key)
    except KeyError:
        value = container[key] = array()
        return value


def get_set_dict(dict_: StrDict, key: str, /) -> StrDict:
    try:
        return get_dict(dict_, key)
    except KeyError:
        value = dict_[key] = {}
        return value


def get_set_list_dicts(dict_: StrDict, key: str, /) -> list[StrDict]:
    try:
        return get_list_dicts(dict_, key)
    except KeyError:
        value = dict_[key] = []
        return value


def get_set_list_strs(dict_: StrDict, key: str, /) -> list[str]:
    try:
        return get_list_strs(dict_, key)
    except KeyError:
        value = dict_[key] = []
        return value


def get_set_table(container: ContainerLike, key: str, /) -> Table:
    try:
        return get_table(container, key)
    except KeyError:
        value = container[key] = table()
        return value


##


def get_version_from_path(*, path: PathLike = BUMPVERSION_TOML) -> Version3:
    return _get_version_from_toml_text(read_text(path))


def get_version_origin_master(*, path: PathLike = BUMPVERSION_TOML) -> Version3:
    with suppress(CalledProcessError):
        text = run("git", "tag", "--points-at", "origin/master", return_=True)
        for line in text.splitlines():
            with suppress(Version3Error):
                return Version3.parse(line)
    try:
        text = run("git", "show", f"origin/master:{path}", return_=True)
    except CalledProcessError:
        msg = "Unable to get the version of origin/master"
        raise ValueError(msg) from None
    return _get_version_from_toml_text(text)


def _get_version_from_toml_text(text: str, /) -> Version3:
    try:
        doc = tomlkit.parse(text)
        tool = get_table(doc, "tool")
        bumpversion = get_table(tool, "bumpversion")
        version = bumpversion["current_version"]
        return Version3.parse(str(version))
    except (ParseError, KeyError, Version3Error):
        msg = f"Unable to get the version from {text!r}"
        raise ValueError(msg) from None


##


def get_version_set(
    *, index: MaybeSequenceStr | None = None, native_tls: bool = False
) -> VersionSet:
    out: StrDict = {}
    for item in uv_pip_list(exclude_editable=True, index=index, native_tls=native_tls):
        match item.version, item.latest_version:
            case Version2(), Version2() | None:
                out[item.name] = max_nullable([item.version, item.latest_version])
            case Version3(), Version3() | None:
                out[item.name] = max_nullable([item.version, item.latest_version])
            case _:
                raise TypeError(item.version, item.latest_version)
    return out


##


def merge_paths(
    *paths: PathLike, target: PathLike, also_ok: MaybeSequence[PathLike] | None = None
) -> list[Path]:
    paths_use = list(map(Path, paths))
    target = Path(target)
    if target == PRE_COMMIT_CONFIG_YAML:
        msg = f"Invalid target; got {str(target)!r}"
        raise ValueError(msg)
    out: set[Path] = set()
    all_ok: set[Path] = {PRE_COMMIT_CONFIG_YAML}
    if also_ok is not None:
        all_ok.update(map(Path, always_iterable(also_ok)))
    for p in paths_use:
        if p.name == target.name:
            out.add(p)
        elif any(p.name == other.name for other in all_ok):
            out.add(p.parent / target)
        else:
            msg = f"Invalid path; got {str(p)!r}"
            raise ValueError(msg)
    return sorted(out)


##


def path_throttle_cache(name: str, /) -> Path:
    cwd_name = Path.cwd().name
    return PATH_CACHE / "throttle" / f"{name}--{cwd_name}"


##


def re_insert_dict(dict_: StrDict, keys: list[str], /) -> None:
    copy = dict_.copy()
    dict_.clear()
    for key in keys:
        with suppress(KeyError):
            dict_[key] = copy[key]


def re_insert_hook_dict(hook: StrDict, repo: StrDict, /) -> None:
    if repo["repo"] == "local":
        keys = PRE_COMMIT_HOOKS_HOOK_KEYS
    else:
        keys = PRE_COMMIT_CONFIG_HOOK_KEYS
    re_insert_dict(hook, keys)


##


def run_all(*funcs: Callable[[], bool]) -> bool:
    results = [f() for f in funcs]
    return all(results)


def run_all_maybe_raise(*funcs: Callable[[], bool]) -> None:
    if not run_all(*funcs):
        raise SystemExit(1)


##


def run_prettier(path: PathLike, /) -> None:
    with suppress(RunError):
        run("prettier", "-w", str(path))


def run_taplo(path: PathLike, /) -> None:
    with suppress(RunError):
        run(
            "taplo",
            "format",
            "--option",
            "indent_tables=true",
            "--option",
            "indent_entries=true",
            "--option",
            "reorder_keys=true",
            str(path),
        )


##


def set_version(version: Version3, /, *, path: PathLike = BUMPVERSION_TOML) -> None:
    run("bump-my-version", "replace", "--new-version", str(version), str(path))


##


def write_text_and_add_modification(
    path: PathLike, text: str, /, *, modifications: MutableSet[Path] | None = None
) -> None:
    write_text(path, text, overwrite=True)
    add_modification(path, modifications=modifications)


##


@contextmanager
def yield_immutable_write_context[T](
    path: PathLike,
    loads: Callable[[str], T],
    get_default: Callable[[], T],
    dumps: Callable[[T], str],
    /,
    *,
    modifications: MutableSet[Path] | None = None,
    is_equal: Callable[[T, T], bool] = eq,
) -> Iterator[_WriteContext[T]]:
    try:
        current = read_text(path)
    except ReadTextError:
        current = None
        input_ = get_default()
        output = get_default()
    else:
        input_ = loads(current)
        output = loads(current)
    yield (context := _WriteContext(input=input_, output=output))
    if (current is None) or not is_equal(context.output, loads(current)):
        write_text_and_add_modification(
            path, dumps(context.output), modifications=modifications
        )


@dataclass(kw_only=True, slots=True)
class _WriteContext[T]:
    input: T
    output: T


##


@contextmanager
def yield_json_dict(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[StrDict]:
    with yield_mutable_write_context(
        path, json.loads, dict, json.dumps, modifications=modifications
    ) as dict_:
        yield dict_


##


@contextmanager
def yield_mutable_write_context[T](
    path: PathLike,
    loads: Callable[[str], T],
    get_default: Callable[[], T],
    dumps: Callable[[T], str],
    /,
    *,
    modifications: MutableSet[Path] | None = None,
    is_equal: Callable[[T, T], bool] = eq,
) -> Iterator[T]:
    with yield_immutable_write_context(
        path, loads, get_default, dumps, modifications=modifications, is_equal=is_equal
    ) as context:
        yield context.output


##


@contextmanager
def yield_python_file(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[_WriteContext[Module]]:
    def is_equal(x: Module, y: Module, /) -> bool:
        return are_equal_modulo_new_line(x.code, y.code)

    with yield_immutable_write_context(
        path,
        parse_module,
        lambda: Module(body=[]),
        lambda module: module.code,
        modifications=modifications,
        is_equal=is_equal,
    ) as context:
        yield context


##


@contextmanager
def yield_text_file(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[_WriteContext[str]]:
    with yield_immutable_write_context(
        path,
        str,
        lambda: "",
        str,
        modifications=modifications,
        is_equal=are_equal_modulo_new_line,
    ) as context:
        yield context


##


@contextmanager
def yield_toml_doc(
    path: PathLike,
    /,
    *,
    modifications: MutableSet[Path] | None = None,
    is_equal: Callable[[TOMLDocument, TOMLDocument], bool] = eq,
) -> Iterator[TOMLDocument]:
    with yield_mutable_write_context(
        path,
        tomlkit.parse,
        document,
        tomlkit.dumps,
        modifications=modifications,
        is_equal=is_equal,
    ) as doc:
        yield doc
    run_taplo(path)


##


@contextmanager
def yield_tool(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[Table]:
    with yield_toml_doc(path, modifications=modifications) as doc:
        yield get_set_table(doc, "tool")


@contextmanager
def yield_tool_uv(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[Table]:
    with yield_tool(path, modifications=modifications) as table:
        yield get_set_table(table, "uv")


@contextmanager
def yield_tool_uv_index(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[AoT]:
    with yield_tool_uv(path, modifications=modifications) as table:
        yield get_set_aot(table, "index")


##


@contextmanager
def yield_yaml_dict(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[StrDict]:
    with yield_mutable_write_context(
        path,
        yaml.safe_load,
        dict,
        partial(yaml.safe_dump, sort_keys=False),
        modifications=modifications,
    ) as dict_:
        yield dict_
    run_prettier(path)


##


__all__ = [
    "PyProjectDependencies",
    "add_update_certificates",
    "are_equal_modulo_new_line",
    "ensure_contains",
    "ensure_contains_partial_dict",
    "ensure_contains_partial_str",
    "ensure_new_line",
    "ensure_not_contains",
    "get_aot",
    "get_array",
    "get_dict",
    "get_list_dicts",
    "get_list_strs",
    "get_partial_dict",
    "get_partial_str",
    "get_pyproject_dependencies",
    "get_set_aot",
    "get_set_array",
    "get_set_dict",
    "get_set_list_dicts",
    "get_set_list_strs",
    "get_set_partial_dict",
    "get_set_partial_dict",
    "get_set_table",
    "get_table",
    "get_version_from_path",
    "get_version_origin_master",
    "get_version_set",
    "merge_paths",
    "path_throttle_cache",
    "re_insert_dict",
    "re_insert_hook_dict",
    "run_all",
    "run_all_maybe_raise",
    "run_prettier",
    "run_taplo",
    "set_version",
    "write_text_and_add_modification",
    "yield_immutable_write_context",
    "yield_json_dict",
    "yield_mutable_write_context",
    "yield_python_file",
    "yield_text_file",
    "yield_toml_doc",
    "yield_tool",
    "yield_tool_uv",
    "yield_tool_uv_index",
    "yield_yaml_dict",
]

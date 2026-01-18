from __future__ import annotations

import json
from collections.abc import Iterator, MutableSet
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Any, Literal, assert_never, overload

import tomlkit
from libcst import Module, parse_module
from tomlkit import TOMLDocument, aot, array, document, parse, string, table
from tomlkit.items import AoT, Array, Table
from utilities.atomicwrites import writer
from utilities.concurrent import concurrent_map
from utilities.functions import ensure_class, ensure_str, get_class_name, get_func_name
from utilities.iterables import OneEmptyError, one
from utilities.packaging import Requirement
from utilities.subprocess import run
from utilities.types import PathLike, StrDict
from utilities.typing import is_str_dict
from utilities.version import Version, parse_version

from pre_commit_hooks.constants import (
    FORMATTER_PRIORITY,
    LINTER_PRIORITY,
    PATH_CACHE,
    PRE_COMMIT_CONFIG_YAML,
    PYPROJECT_TOML,
    YAML_INSTANCE,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, MutableSet

    from utilities.types import PathLike, StrDict

    from pre_commit_hooks.types import ArrayLike, ContainerLike, FuncRequirement


def add_pre_commit_config_repo(
    url: str,
    id_: str,
    /,
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
    rev: bool = False,
    name: str | None = None,
    entry: str | None = None,
    language: str | None = None,
    files: str | None = None,
    types_or: list[str] | None = None,
    args: tuple[Literal["add", "exact"], list[str]] | None = None,
    type_: Literal["formatter", "linter"] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos_list = get_set_list_dicts(dict_, "repos")
        repo_dict = ensure_contains_partial_dict(
            repos_list, {"repo": url}, extra={"rev": "master"} if rev else {}
        )
        hooks_list = get_set_list_dicts(repo_dict, "hooks")
        hook_dict = ensure_contains_partial_dict(hooks_list, {"id": id_})
        if name is not None:
            hook_dict["name"] = name
        if entry is not None:
            hook_dict["entry"] = entry
        if language is not None:
            hook_dict["language"] = language
        if files is not None:
            hook_dict["files"] = files
        if types_or is not None:
            hook_dict["types_or"] = types_or
        if args is not None:
            match args:
                case "add", list() as args_i:
                    hook_args = get_set_list_strs(hook_dict, "args")
                    ensure_contains(hook_args, *args_i)
                case "exact", list() as args_i:
                    hook_dict["args"] = args_i
                case never:
                    assert_never(never)
        match type_:
            case "formatter":
                hook_dict["priority"] = FORMATTER_PRIORITY
            case "linter":
                hook_dict["priority"] = LINTER_PRIORITY
            case None:
                ...
            case never:
                assert_never(never)
    run_prettier(path)


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
    container: list[StrDict], partial: StrDict, /, *, extra: StrDict | None = None
) -> StrDict:
    try:
        return get_partial_dict(container, partial)
    except OneEmptyError:
        dict_ = partial | ({} if extra is None else extra)
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


def get_partial_dict(iterable: Iterable[StrDict], dict_: StrDict, /) -> StrDict:
    return one(i for i in iterable if _is_partial_dict(dict_, i))


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

    def apply(self, func: FuncRequirement, /) -> None:
        if (deps := self.dependencies) is not None:
            self._apply_to_array(deps, func)
        if (opt_depedencies := self.opt_dependencies) is not None:
            for deps in opt_depedencies.values():
                self._apply_to_array(deps, func)
        if (dep_grps := self.dep_groups) is not None:
            for deps in dep_grps.values():
                self._apply_to_array(deps, func)

    def _apply_to_array(self, array: Array, func: FuncRequirement, /) -> None:
        strs = list(map(ensure_str, array))
        reqs = list(map(Requirement, strs))
        results = list(map(func, reqs))
        new_strs = list(map(str, results))
        strings = list(map(string, new_strs))
        array.clear()
        ensure_contains(array, *strings)


##


def path_throttle_cache(func: Callable[..., Any]) -> Path:
    func_name = get_func_name(func)
    cwd_name = Path.cwd().name
    return PATH_CACHE / "throttle" / f"{func_name}--{cwd_name}"


##


def run_all_maybe_raise(*funcs: Callable[[], bool]) -> None:
    """Run all of a set of jobs."""

    results = concurrent_map(_apply, funcs, parallelism="threads")
    if not all(results):
        raise SystemExit(1)


def _apply[T](func: Callable[[], T], /) -> T:
    return func()


##


def run_prettier(path: PathLike, /) -> None:
    with suppress(CalledProcessError):
        run("prettier", "-w", str(path))


##


def write_text(
    path: PathLike, text: str, /, *, modifications: MutableSet[Path] | None = None
) -> None:
    with writer(path, overwrite=True) as temp:
        _ = temp.write_text(ensure_new_line(text))
    if modifications is not None:
        modifications.add(Path(path))


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
) -> Iterator[_WriteContext[T]]:
    try:
        current = Path(path).read_text()
    except FileNotFoundError:
        current = None
        input_ = get_default()
        output = get_default()
    else:
        input_ = loads(current)
        output = loads(current)
    yield (context := _WriteContext(input=input_, output=output))
    if current is None:
        write_text(path, dumps(context.output), modifications=modifications)
    else:
        match context.output, loads(current):
            case Module() as output_module, Module() as current_module:
                if not are_equal_modulo_new_line(
                    output_module.code, current_module.code
                ):
                    write_text(path, dumps(output_module), modifications=modifications)
            case TOMLDocument() as output_doc, TOMLDocument() as current_doc:
                if not (output_doc == current_doc):  # noqa: SIM201
                    write_text(path, dumps(output_doc), modifications=modifications)
            case str() as output_text, str() as current_text:
                if not are_equal_modulo_new_line(output_text, current_text):
                    write_text(path, dumps(output_text), modifications=modifications)
            case output_obj, current_obj:
                if output_obj != current_obj:
                    write_text(path, dumps(output_obj), modifications=modifications)
            case never:
                assert_never(never)


@dataclass(kw_only=True, slots=True)
class _WriteContext[T]:
    input: T
    output: T


##


def yaml_dump(obj: Any, /) -> str:
    stream = StringIO()
    YAML_INSTANCE.dump(obj, stream)
    return stream.getvalue()


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
def yield_pyproject_toml(
    *, modifications: MutableSet[Path] | None = None
) -> Iterator[TOMLDocument]:
    with yield_toml_doc(PYPROJECT_TOML, modifications=modifications) as doc:
        yield doc


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
) -> Iterator[T]:
    with yield_immutable_write_context(
        path, loads, get_default, dumps, modifications=modifications
    ) as context:
        yield context.output


##


@contextmanager
def yield_python_file(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[_WriteContext[Module]]:
    with yield_immutable_write_context(
        path,
        parse_module,
        lambda: Module(body=[]),
        lambda module: module.code,
        modifications=modifications,
    ) as context:
        yield context


##


@contextmanager
def yield_text_file(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[_WriteContext[str]]:
    with yield_immutable_write_context(
        path, str, lambda: "", str, modifications=modifications
    ) as context:
        yield context


##


@contextmanager
def yield_toml_doc(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[TOMLDocument]:
    with yield_mutable_write_context(
        path, tomlkit.parse, document, tomlkit.dumps, modifications=modifications
    ) as doc:
        yield doc


##


@contextmanager
def yield_yaml_dict(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> Iterator[StrDict]:
    with yield_mutable_write_context(
        path, YAML_INSTANCE.load, dict, yaml_dump, modifications=modifications
    ) as dict_:
        yield dict_


def get_version_zz(source: Path | str | bytes | TOMLDocument, /) -> Version:
    """Get the `[tool.bumpversion]` version from a TOML file."""
    match source:
        case Path() as path:
            return get_version_zz(path.read_text())
        case str() | bytes() as text:
            return get_version_zz(parse(text))
        case TOMLDocument() as doc:
            try:
                tool = doc["tool"]
            except KeyError:
                msg = "Key 'tool' does not exist"
                raise GetVersionError(msg) from None
            if not isinstance(tool, Table):
                msg = "`tool` is not a Table"
                raise GetVersionError(msg)
            try:
                bumpversion = tool["bumpversion"]
            except KeyError:
                msg = "Key 'bumpversion' does not exist"
                raise GetVersionError(msg) from None
            if not isinstance(bumpversion, Table):
                msg = "`bumpversion` is not a Table"
                raise GetVersionError(msg)
            try:
                version = bumpversion["current_version"]
            except KeyError:
                msg = "Key 'current_version' does not exist"
                raise GetVersionError(msg) from None
            if not isinstance(version, str):
                msg = f"`version` is not a string; got {get_class_name(version)!r}"
                raise GetVersionError(msg)
            return parse_version(version)
        case never:
            assert_never(never)


class GetVersionError(Exception): ...


##


__all__ = [
    "PyProjectDependencies",
    "add_pre_commit_config_repo",
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
    "get_set_table",
    "get_table",
    "get_version_zz",
    "path_throttle_cache",
    "run_all_maybe_raise",
    "run_prettier",
    "write_text",
    "yaml_dump",
    "yield_immutable_write_context",
    "yield_json_dict",
    "yield_mutable_write_context",
    "yield_pyproject_toml",
    "yield_python_file",
    "yield_text_file",
    "yield_toml_doc",
    "yield_yaml_dict",
]

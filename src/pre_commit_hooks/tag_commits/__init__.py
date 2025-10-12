from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import utilities.click
from click import command, option
from git import Commit, GitCommandError, Repo
from loguru import logger
from utilities.tzlocal import LOCAL_TIME_ZONE_NAME
from utilities.whenever import from_timestamp, get_now_local

from pre_commit_hooks.common import (
    DEFAULT_MODE,
    GetVersionError,
    Mode,
    get_toml_path,
    get_version,
    mode_option,
    run_all,
    run_every_option,
    throttled_run,
)

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from whenever import DateTimeDelta, ZonedDateTime


@command()
@run_every_option
@option(
    "--max-age", type=utilities.click.DateTimeDelta(), default=None, show_default=True
)
@mode_option
def main(
    *,
    run_every: DateTimeDelta | None = None,
    max_age: DateTimeDelta | None = None,
    mode: Mode = DEFAULT_MODE,
) -> bool:
    """CLI for the `tag-commits` hook."""
    return throttled_run("tag-commits", run_every, _process, max_age=max_age, mode=mode)


def _process(
    *, max_age: DateTimeDelta | None = None, mode: Mode = DEFAULT_MODE
) -> bool:
    repo = Repo(".", search_parent_directories=True)
    tagged = {tag.commit.hexsha for tag in repo.tags}
    min_date_time = None if max_age is None else (get_now_local() - max_age)
    commits = reversed(list(repo.iter_commits(repo.refs["origin/master"])))
    results = (
        _process_commit(c, tagged, repo, min_date_time=min_date_time, mode=mode)
        for c in commits
    )
    return run_all(results)


def _process_commit(
    commit: Commit,
    tagged: AbstractSet[str],
    repo: Repo,
    /,
    *,
    min_date_time: ZonedDateTime | None = None,
    mode: Mode = DEFAULT_MODE,
) -> bool:
    if (commit.hexsha in tagged) or (
        (min_date_time is not None) and (_get_date_time(commit) < min_date_time)
    ):
        return True
    try:
        return _tag_commit(commit, repo, mode=mode)
    except TagCommitsError as error:
        logger.exception("%s", error.args[0])
        return False


def _get_date_time(commit: Commit, /) -> ZonedDateTime:
    return from_timestamp(commit.committed_date, time_zone=LOCAL_TIME_ZONE_NAME)


def _tag_commit(
    commit: Commit, repo: Repo, /, *, mode: Mode = DEFAULT_MODE
) -> Literal[True]:
    sha = commit.hexsha[:7]
    date = _get_date_time(commit)
    desc = f"{sha!r} ({date})"
    path = get_toml_path(mode)
    try:
        joined = commit.tree.join(str(path))
    except KeyError:
        msg = f"Failed to tag {desc}; {str(path)!r} does not exist"
        raise TagCommitsError(msg) from None
    text = joined.data_stream.read()
    try:
        version = get_version(text)
    except GetVersionError as error:
        msg = f"Failed to tag {desc}; error getting veresion: {error.args[0]}"
        raise TagCommitsError(msg) from None
    str_ver = str(version)
    try:
        existing = repo.tags[str_ver]
    except IndexError:
        pass
    else:
        repo.delete_tag(existing)
    try:
        tag = repo.create_tag(str_ver, ref=sha)
    except GitCommandError as error:
        msg = f"Failed to tag {desc}; error creating tag: {error.stderr.strip()}"
        raise TagCommitsError(msg) from None
    logger.info(f"Tagging {desc} as {str_ver!r}...")
    try:
        _ = repo.remotes.origin.push(f"refs/tags/{tag.name}")
    except GitCommandError as error:
        msg = f"Failed to tag {desc}; error pushing tag: {error.stderr.strip()}"
        raise TagCommitsError(msg) from None
    return True


class TagCommitsError(Exception): ...


__all__ = ["main"]

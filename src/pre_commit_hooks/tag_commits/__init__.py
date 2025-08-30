from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from git import Commit, GitCommandError, Repo
from loguru import logger
from utilities.hashlib import md5_hash
from utilities.pathlib import get_repo_root
from utilities.tzlocal import LOCAL_TIME_ZONE_NAME
from utilities.whenever import MINUTE, YEAR, from_timestamp, get_now_local
from whenever import ZonedDateTime
from xdg_base_dirs import xdg_cache_home

from pre_commit_hooks.common import get_version

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet


@command()
def main() -> bool:
    """CLI for the `tag_commits` hook."""
    return _process()


def _process() -> bool:
    last = _get_last_run()
    min_dt = get_now_local() - 5 * MINUTE
    if (last is not None) and (min_dt <= last):
        return True
    return _process_commits()


def _get_last_run() -> ZonedDateTime | None:
    hash_ = md5_hash(get_repo_root())
    path = xdg_cache_home().joinpath("tag-commits", hash_)
    try:
        text = path.read_text()
    except FileNotFoundError:
        return None
    try:
        return ZonedDateTime.parse_common_iso(text.strip("\n"))
    except ValueError:
        return None


def _process_commits() -> bool:
    repo = Repo(".", search_parent_directories=True)
    tagged = {tag.commit.hexsha for tag in repo.tags}
    min_dt = get_now_local() - YEAR
    commits = reversed(list(repo.iter_commits(repo.refs["origin/master"])))
    results = [_process_commit(c, tagged, min_dt, repo) for c in commits]  # run all
    return all(results)


def _process_commit(
    commit: Commit, tagged: AbstractSet[str], min_date: ZonedDateTime, repo: Repo, /
) -> bool:
    if (commit.hexsha in tagged) or (_get_date_time(commit) < min_date):
        return True
    try:
        _tag_commit(commit, repo)
    except GitCommandError:
        return False
    return True


def _get_date_time(commit: Commit, /) -> ZonedDateTime:
    return from_timestamp(commit.committed_date, time_zone=LOCAL_TIME_ZONE_NAME)


def _tag_commit(commit: Commit, repo: Repo, /) -> None:
    sha = commit.hexsha[:7]
    date = _get_date_time(commit)
    try:
        joined = commit.tree.join("pyproject.toml")
    except KeyError:
        logger.exception(f"`pyproject.toml` not found; failed to tag {sha!r} ({date})")
        return
    text = joined.data_stream.read()
    version = get_version(text, desc=f"'pyproject.toml' @ {sha}")
    try:
        tag = repo.create_tag(str(version), ref=sha)
    except GitCommandError as error:
        desc = error.stderr.strip("\n").strip()
        logger.exception(f"Failed to tag {sha!r} ({date}) due to {desc}")
        return
    logger.info(f"Tagging {sha!r} ({date}) as {str(version)!r}...")
    _ = repo.remotes.origin.push(f"refs/tags/{tag.name}")


__all__ = ["main"]

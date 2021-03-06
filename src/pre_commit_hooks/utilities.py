from itertools import dropwhile
from typing import Iterable
from typing import Iterator

from more_itertools import split_when


def split_gitignore_lines(lines: Iterable[str]) -> Iterator[list[str]]:
    def is_content(line: str) -> bool:
        return bool(line) and not line.startswith("#")

    def is_not_content(line: str) -> bool:
        return not is_content(line)

    for group in split_when(
        lines, lambda c, n: is_content(c) and not is_content(n)
    ):
        yield list(dropwhile(is_not_content, group))

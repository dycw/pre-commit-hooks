from pytest import mark

from pre_commit_hooks.utilities import split_gitignore_lines


@mark.parametrize(
    ["lines", "expected"],
    [
        ([], []),
        (["# header", "1", "2"], [["1", "2"]]),
        (
            ["# header 1", "1", "2", "", "# header 2", "3", "4"],
            [["1", "2"], ["3", "4"]],
        ),
    ],
)
def test_split_gitignore_lines(
    lines: list[str], expected: list[list[str]]
) -> None:
    assert list(split_gitignore_lines(lines)) == expected

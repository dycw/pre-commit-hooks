from subprocess import CalledProcessError  # noqa:S404
from subprocess import check_call  # noqa:S404
from sys import exit


def main() -> int:
    try:
        check_call(["no-commit-to-branch"])  # noqa:S603,S607
    except CalledProcessError:
        return 1
    else:
        return 0


if __name__ == "__main__":
    exit(main())

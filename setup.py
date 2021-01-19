from setuptools import find_packages
from setuptools import setup


setup(
    name="dummy-package",
    entry_points={
        "console_scripts": [
            "do-python = hooks.do_python:main",
            "no-commit = hooks.no_commit:main",
            "text = hooks.text:main",
            "universal = hooks.universal:main",
        ],
    },
    include_package_data=True,
    install_requires=[
        # generic
        "pre-commit-hooks",
        # formatters
        "add-trailing-comma",
        "autoflake",
        "black",
        "pyupgrade",
        "reorder-python-imports",
        "yesqa",
        # linters
        "flake8",
        "mypy",
        # flake8
        "dlint",
        "flake8-absolute-import",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-builtins",
        "flake8-commas",
        "flake8-comprehensions",
        "flake8-debugger",
        "flake8-eradicate",
        "flake8-executable",
        "flake8-fine-pytest",
        "flake8-fixme",
        "flake8-future-import",
        "flake8-implicit-str-concat",
        "flake8-mutable",
        "flake8-print",
        "flake8-pytest-style",
        "flake8-simplify",
        "flake8-string-format",
        "flake8-todo",
        "flake8-typing-imports",
        "flake8-unused-arguments",
        "pep8-naming",
    ],
    packages=find_packages(),
    package_data={"python": [".flake8", "mypy.ini"]},
    url="https://github.com/dycw/pre-commit-hooks",
)

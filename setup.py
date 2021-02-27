from setuptools import find_packages
from setuptools import setup

setup(
    name="dummy-package",
    entry_points={
        "console_scripts": [
            "check-settings = hooks.check_settings:main",
        ],
    },
    include_package_data=True,
    install_requires=[
        "gitpython",
        "pyyaml",
        "toml",
    ],
    packages=find_packages(where="src"),
    url="https://github.com/dycw/pre-commit-hooks",
)

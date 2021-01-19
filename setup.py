from setuptools import find_packages
from setuptools import setup


def foo(aaaaaaaaaa, bbbbbbbbbb, cccccccccccccc, ddddddddddd, eeeeeeeee, fffffff) -> None:
    pass


setup(
    name="dycw-pre-commit-hooks",
    description="DYCW's pre-commit hooks",
    url="https://github.com/dycw/pre-commit-hooks",
    author="Derek Wan",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    packages=find_packages(),
    install_requires=["black"],
    # not sure:     entry_points={
    # not sure:         'console_scripts': [
    # not sure:             'terraform_docs_replace = pre_commit_hooks.terraform_docs_replace:main',
    # not sure:         ],
    # not sure:     },
)

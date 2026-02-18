from __future__ import annotations

import utilities.click
from utilities.click import ListStrs, SecretStr, Str, argument, flag, option

certificates_flag = flag("--certificates", default=False)
description_option = option("--description", type=Str(), default=None)
gitea_flag = flag("--gitea", default=False)
index_option = option("--index", type=ListStrs(), default=None)
index_name_option = option("--index-name", type=Str(), default=None)
index_password_option = option("--index-password", type=SecretStr(), default=None)
index_username_option = option("--index-username", type=Str(), default=None)
native_tls_flag = flag("--native-tls", default=False)
package_name_option = option("--package-name", type=Str(), default=None)
paths_argument = argument("paths", nargs=-1, type=utilities.click.Path())
python_flag = flag("--python", default=False)
repo_name_option = option("--repo-name", type=Str(), default=None)
throttle_flag = flag("--throttle", default=True)
token_checkout_option = option("--token-checkout", type=SecretStr(), default=None)
token_github_option = option("--token-github", type=SecretStr(), default=None)
version_option = option("--version", type=Str(), default=None)


__all__ = [
    "certificates_flag",
    "description_option",
    "gitea_flag",
    "index_name_option",
    "index_option",
    "index_password_option",
    "index_username_option",
    "native_tls_flag",
    "package_name_option",
    "paths_argument",
    "python_flag",
    "repo_name_option",
    "throttle_flag",
    "token_checkout_option",
    "token_github_option",
    "version_option",
]

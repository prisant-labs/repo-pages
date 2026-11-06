#!/usr/bin/env python3
# Repo Pages: https://github.com/prisant-labs/repo-pages
# MIT License. See LICENSE in that repository.

"""
Check that a repository can publish before the action builds anything.

It refuses a private repository unless told otherwise, because a GitHub Pages
site can be public even when its repository is private. It also turns the setup
mistakes every adopter can make into errors that say exactly what to change.

Uses only the Python standard library. Runs inside the action, and reads the
GITHUB_* variables that GitHub Actions sets.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Callable

ENABLE_COMMAND = 'gh api -X POST "repos/{repo}/pages" -f build_type=workflow'


def check(fetch: Callable[[str], tuple[int, dict]], repo: str, server: str, env: dict, allow_private: bool) -> list[str]:
    """Return every reason this repository cannot publish. An empty list means it can."""
    settings = f"{server}/{repo}/settings/pages"

    status, info = fetch(f"repos/{repo}")
    if status != 200:
        return [f"Could not read this repository (HTTP {status}), so its visibility is unknown. Nothing was published."]
    if info.get("private") and not allow_private:
        return [
            "This repository is private, and a GitHub Pages site can be public even so. "
            'Nothing was published. To publish anyway, set allow-private-repository to "true".'
        ]

    errors = []
    if not env.get("ACTIONS_ID_TOKEN_REQUEST_URL"):
        errors.append("Add 'id-token: write' to the permissions of the job that runs this action.")

    status, pages = fetch(f"repos/{repo}/pages")
    if status == 404:
        errors.append(
            f"GitHub Pages is not turned on. Set Source to 'GitHub Actions' at {settings}, "
            f"or run: {ENABLE_COMMAND.format(repo=repo)}"
        )
    elif status == 403:
        errors.append("Add 'pages: write' to the permissions of the job that runs this action.")
    elif status != 200:
        errors.append(f"Could not read the GitHub Pages settings (HTTP {status}).")
    elif pages.get("build_type") != "workflow":
        errors.append(f"GitHub Pages is publishing from a branch. Set Source to 'GitHub Actions' at {settings}.")
    return errors


def github_fetch(api: str, token: str) -> Callable[[str], tuple[int, dict]]:
    def fetch(path: str) -> tuple[int, dict]:
        request = urllib.request.Request(
            f"{api}/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, {}
        except urllib.error.URLError:
            return 0, {}

    return fetch


def main() -> int:
    env = os.environ
    fetch = github_fetch(env.get("GITHUB_API_URL", "https://api.github.com"), env.get("REPO_PAGES_TOKEN", ""))
    errors = check(
        fetch,
        repo=env["GITHUB_REPOSITORY"],
        server=env.get("GITHUB_SERVER_URL", "https://github.com"),
        env=dict(env),
        allow_private=env.get("REPO_PAGES_ALLOW_PRIVATE", "false").strip().lower() == "true",
    )
    for error in errors:
        print(f"::error title=Repo Pages::{error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

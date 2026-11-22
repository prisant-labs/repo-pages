#!/usr/bin/env python3
# Repo Pages: https://github.com/prisant-labs/repo-pages
# MIT License. See LICENSE in that repository.

"""
Check that a repository can publish before the action builds anything.

It refuses a private repository whose GitHub Pages site is public, unless told
otherwise, because a site can be public even when its repository is private. A
private site publishes without any setting. It also turns the setup mistakes every
adopter can make into errors that say exactly what to change.

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
MAKE_PRIVATE_COMMAND = 'gh api -X PUT "repos/{repo}/pages" -F public=false'


def check(
    fetch: Callable[[str], tuple[int, dict]],
    repo: str,
    server: str,
    env: dict,
    allow_private: bool,
    require_private: bool = False,
) -> list[str]:
    """Return every reason this repository cannot publish. An empty list means it can."""
    settings = f"{server}/{repo}/settings/pages"

    status, info = fetch(f"repos/{repo}")
    if status != 200:
        return [f"Could not read this repository (HTTP {status}), so its visibility is unknown. Nothing was published."]

    pages_status, pages = fetch(f"repos/{repo}/pages")
    refusal = site_refusal(info, pages_status, pages, repo, settings, allow_private, require_private)
    if refusal:
        return [refusal]

    errors = []
    if not env.get("ACTIONS_ID_TOKEN_REQUEST_URL"):
        errors.append("Add 'id-token: write' to the permissions of the job that runs this action.")

    if pages_status == 404:
        errors.append(
            f"GitHub Pages is not turned on. Set Source to 'GitHub Actions' at {settings}, "
            f"or run: {ENABLE_COMMAND.format(repo=repo)}"
        )
    elif pages_status == 403:
        errors.append("Add 'pages: write' to the permissions of the job that runs this action.")
    elif pages_status != 200:
        errors.append(f"Could not read the GitHub Pages settings (HTTP {pages_status}).")
    elif pages.get("build_type") != "workflow":
        errors.append(f"GitHub Pages is publishing from a branch. Set Source to 'GitHub Actions' at {settings}.")
    return errors


def site_refusal(
    info: dict, pages_status: int, pages: dict, repo: str, settings: str, allow_private: bool, require_private: bool
) -> str:
    """Return why the site's visibility stops this run, or an empty string if it does not.

    Only a "public" of exactly False counts as private. A missing or odd value counts
    as public, so a change in GitHub's response can only refuse, never leak.
    """
    private = bool(info.get("private"))
    if not require_private and (not private or allow_private):
        return ""
    if pages_status != 200:
        # The Pages checks in check() report why the settings could not be read, and
        # that error stops the run. The next run checks visibility once they can be read.
        return ""

    public = pages.get("public")
    if public is False:
        return ""

    if require_private:
        if not private:
            return (
                'require-private-site is "true", but this repository is public, and a site from a public '
                "repository is always public. Nothing was published. Make the repository private or internal, "
                "or remove require-private-site."
            )
        if public is True:
            return (
                'require-private-site is "true", but this repository\'s GitHub Pages site is public. '
                "Nothing was published. Private sites need GitHub Enterprise Cloud, so if your plan has none, "
                f"remove require-private-site. Otherwise, set GitHub Pages visibility to Private at {settings}, "
                f"or run: {MAKE_PRIVATE_COMMAND.format(repo=repo)}"
            )
        return (
            'require-private-site is "true", but GitHub did not report whether this repository\'s GitHub Pages '
            f"site is public. Nothing was published. Check that GitHub Pages visibility is Private at {settings}. "
            "If your GitHub plan has no private sites, remove require-private-site."
        )

    if info.get("visibility") == "internal":
        kind = "This repository is internal. GitHub counts internal repositories as private."
    else:
        kind = "This repository is private."
    if public is True:
        return (
            f"{kind} Its GitHub Pages site is public, so anyone on the internet could read it. "
            f"Nothing was published. Set GitHub Pages visibility to Private at {settings}, which needs "
            'GitHub Enterprise Cloud. To publish it publicly anyway, set allow-private-repository to "true".'
        )
    return (
        f"{kind} GitHub did not report whether its GitHub Pages site is public, so repo-pages treats "
        f"it as public. Nothing was published. Check GitHub Pages visibility at {settings}. "
        'To publish anyway, set allow-private-repository to "true".'
    )


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
    # require-private-site is a safety switch, so a typo must not quietly turn it off.
    require = env.get("REPO_PAGES_REQUIRE_PRIVATE_SITE", "false").strip()
    if require.lower() not in ("true", "false", ""):
        print(
            f'::error title=Repo Pages::require-private-site must be "true" or "false", not "{require}". '
            "Nothing was published."
        )
        return 1

    fetch = github_fetch(env.get("GITHUB_API_URL", "https://api.github.com"), env.get("REPO_PAGES_TOKEN", ""))
    errors = check(
        fetch,
        repo=env["GITHUB_REPOSITORY"],
        server=env.get("GITHUB_SERVER_URL", "https://github.com"),
        env=dict(env),
        allow_private=env.get("REPO_PAGES_ALLOW_PRIVATE", "false").strip().lower() == "true",
        require_private=require.lower() == "true",
    )
    for error in errors:
        print(f"::error title=Repo Pages::{error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

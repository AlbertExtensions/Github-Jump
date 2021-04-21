"""Jump to github repos at light speed!"""
import time

import json
import os
from typing import Dict, List
from albert import *
from difflib import SequenceMatcher
from github import Github
from os import path
from pathlib import Path

__title__ = "Github Jump"
__version__ = "0.0.1"
__triggers__ = "gj"
__author__ = "Bharat kalluri"
__py_deps__ = ["pygithub", "boltons"]

from github.AuthenticatedUser import AuthenticatedUser
from github.Repository import Repository

icon_path = "{}/icons/{}.png".format(path.dirname(__file__), "repo")
CONFIG_PATH = os.path.join(configLocation(), "gh_token")
CACHE_PATH = os.path.join(dataLocation(), "gh_cache")


def get_token() -> str:
    gh_token_file: Path = Path(CONFIG_PATH)
    if gh_token_file.is_file():
        return gh_token_file.read_text().strip()
    else:
        raise FileNotFoundError


def save_token(github_token: str) -> None:
    with open(CONFIG_PATH, "w") as f:
        f.write(github_token)


def get_repos(github_token: str, cache_override: bool = False) -> list[dict[str, str]]:
    gh_cache_file: Path = Path(CACHE_PATH)
    if cache_override is False and gh_cache_file.is_file():
        print("Getting from cache")
        repo_list = json.loads(gh_cache_file.read_text())
    else:
        print("Cache empty, getting repos")
        g: Github = Github(github_token)
        user_data: AuthenticatedUser = g.get_user()
        starred: list[Repository] = list(user_data.get_starred())
        personal_repos: list[Repository] = list(user_data.get_repos())
        repo_list: list[dict[str, str]] = [
            {
                "name": repo.name,
                "description": repo.description,
                "html_url": repo.html_url,
            }
            for repo in (starred + personal_repos)
        ]
        gh_cache_file.write_text(json.dumps(repo_list))
    return repo_list


def list_safe_get(arr: list, position: int):
    try:
        return arr[position]
    except IndexError:
        return None


def get_search_results(input_query: str, github_token: str) -> List[Item]:
    repo_list: List[Dict] = get_repos(github_token)
    cleaned_query = str(input_query).replace("#", "").replace("!", "")
    repos_with_match_percentage = [
        {
            "match_percentage": SequenceMatcher(
                lambda x: x in [" ", "-"],
                cleaned_query,
                repo["name"].lower(),
            ).ratio(),
            "repo_info": repo,
        }
        for repo in repo_list
    ]
    repos_with_match_percentage.sort(key=lambda x: x.get('match_percentage'), reverse=True)

    results = []
    for repo_with_match_percentage in repos_with_match_percentage:
        repo = repo_with_match_percentage.get('repo_info')
        repo_name = repo.get('name')
        repo_url = repo.get("html_url")
        repo_description = repo.get('description', '')
        if "!" in str(input_query):
            repo_url = repo_url + "/issues"
        elif "#" in str(input_query):
            repo_url = repo_url + "/pulls"
        results.append(
            Item(
                id=__title__,
                icon=icon_path,
                text=repo_name,
                subtext=repo_description,
                actions=[UrlAction("Open in Github", repo_url)],
            )
        )
    return results


def handleQuery(query):

    if query.isTriggered and query.string.strip():

        # avoid rate limiting
        time.sleep(0.3)
        if not query.isValid:
            return

        input_query = query.string.strip()
        input_query_arr = input_query.split(" ")

        if list_safe_get(input_query_arr, 0) == "token":
            gh_token = list_safe_get(input_query_arr, 1)
            return Item(
                id=__title__,
                icon=icon_path,
                text="Save token?",
                subtext=f"Github token: {gh_token} will be saved on enter",
                actions=[
                    FuncAction(text="Save token", callable=lambda: save_token(gh_token))
                ],
            )

        # Require a token to start
        try:
            github_token = get_token()
        except FileNotFoundError:
            return Item(
                id=__title__,
                icon=icon_path,
                text="Token needed",
                subtext="Please give a token by giving gj token [your token]",
            )

        if (
                list_safe_get(input_query_arr, 0) == "cache"
                and list_safe_get(input_query_arr, 1) == "refresh"
        ):
            print("Force refresh cache")
            return Item(
                id=__title__,
                icon=icon_path,
                text="Refresh cache?",
                subtext="Cache will be refreshed on enter",
                actions=[
                    FuncAction(
                        text="Refresh cache",
                        callable=lambda: get_repos(github_token, cache_override=True),
                    )
                ],
            )

        if len(query.string) >= 1:
            return get_search_results(query.string, github_token)
        else:
            return Item(
                id=__title__,
                icon=icon_path,
                text="Github Jump",
                subtext="Jump to repo in Github! Enter more than 2 Characters to begin search.",
            )

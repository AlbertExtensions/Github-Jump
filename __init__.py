"""Jump to github repos at light speed!"""
import json
import os
import time
from os import path
from pathlib import Path

from albertv0 import *
from github import Github

__iid__ = "PythonInterface/v0.1"
__prettyname__ = "Github Jump"
__version__ = "0.1"
__trigger__ = "gj"
__author__ = "Bharat kalluri"
__dependencies__ = ["pygithub", "boltons"]

icon_path = "{}/icons/{}.png".format(path.dirname(__file__), "repo")
CONFIG_PATH = os.path.join(configLocation(), 'gh_token')
CACHE_PATH = os.path.join(dataLocation(), 'gh_cache')


def get_token():
    gh_token_file = Path(CONFIG_PATH)
    if gh_token_file.is_file():
        return gh_token_file.read_text().strip()
    else:
        raise FileNotFoundError


def save_token(github_token: str):
    with open(CONFIG_PATH, 'w') as f:
        f.write(github_token)


def get_repos(github_token, cache_override: bool = False):
    gh_cache_file = Path(CACHE_PATH)
    if cache_override is False and gh_cache_file.is_file():
        print("Getting from cache")
        repo_list = json.loads(gh_cache_file.read_text())
    else:
        print("Cache empty, getting repos")
        repo_list = []
        g = Github(github_token)
        user_data = g.get_user()
        starred = user_data.get_starred()
        personal_repos = user_data.get_repos()
        for repo in personal_repos:
            repo_list.append(repo)
        for repo in starred:
            repo_list.append(repo)
        repo_list = [{
            'name': repo.name,
            'description': repo.description,
            'html_url': repo.html_url
        } for repo in repo_list]
        gh_cache_file.write_text(json.dumps(repo_list))
    return repo_list


def list_safe_get(arr: list, position: int):
    try:
        return arr[position]
    except IndexError:
        return None


def handleQuery(query):
    results = []

    if query.isTriggered and query.string.strip():

        # Require a token to start
        try:
            github_token = get_token()
        except FileNotFoundError:
            return Item(
                id=__prettyname__,
                icon=icon_path,
                text="Token needed",
                subtext="Please give a token by giving gj token [your token]")

        # avoid rate limiting
        time.sleep(0.3)
        if not query.isValid:
            return

        input_query = query.string.strip()
        input_query_arr = input_query.split(" ")

        item = Item(
            id=__prettyname__,
            icon=icon_path,
            completion=query.rawString,
            text=__prettyname__,
            actions=[]
        )

        if list_safe_get(input_query_arr, 0) == "token":
            gh_token = list_safe_get(input_query_arr, 1)
            return Item(
                id=__prettyname__,
                icon=icon_path,
                text="Save token?",
                subtext=f"Github token: {gh_token} will be saved on enter",
                actions=[FuncAction(text="Save token",
                                    callable=lambda: save_token(gh_token))]
            )
        elif list_safe_get(input_query_arr, 0) == 'cache' and list_safe_get(input_query_arr, 1) == 'refresh':
            print("Force refresh cache")
            return Item(
                id=__prettyname__,
                icon=icon_path,
                text="Refresh cache?",
                subtext="Cache will be refreshed on enter",
                actions=[FuncAction(text="Refresh cache",
                                    callable=lambda: get_repos(github_token, cache_override=True))]
            )

        if len(query.string) >= 3:
            repo_list = get_repos(github_token)
            for repo in repo_list:
                cleaned_query = str(input_query).replace('#', '').replace('!', '')
                if cleaned_query in str(repo['html_url']).lower():
                    repo_url = repo['html_url']
                    if "!" in str(input_query):
                        repo_url = repo_url + "/issues"
                    elif "#" in str(input_query):
                        repo_url = repo_url + "/pulls"
                    results.append(Item(
                        id=__prettyname__,
                        icon=icon_path,
                        text=repo['name'],
                        subtext=repo['description'] if repo['description'] else "",
                        actions=[UrlAction("Open in Github", repo_url)])
                    )
        else:
            item.subtext = "Jump to repo in Github! Enter more than 2 Characters to begin search."
            return item
    return results

import time

__iid__ = "PythonInterface/v0.1"
__prettyname__ = "Github Jump"
__version__ = "0.1"
__trigger__ = "gj"
__author__ = "Bharat kalluri"
__dependencies__ = ["pygithub", "boltons"]

from albertv0 import *
from github import Github
from os import path, environ
from boltons import cacheutils

icon_path = "{}/icons/{}.png".format(path.dirname(__file__), "repo")

cache = cacheutils.LRU(max_size=200)


def get_repos():
    print("Trying to get data from cache")
    repo_list = cache.get("REPO_LIST")
    if repo_list is None:
        print("Cache empty, getting repos")
        repo_list = []
        g = Github(environ["GITHUB_TOKEN"])
        user_data = g.get_user()
        starred = user_data.get_starred()
        personal_repos = user_data.get_repos()
        for repo in personal_repos:
            repo_list.append(repo)
        for repo in starred:
            repo_list.append(repo)
        cache["REPO_LIST"] = repo_list
    return repo_list


def handleQuery(query):
    results = []

    if query.isTriggered and query.string.strip():

        # avoid rate limiting
        time.sleep(0.3)
        if not query.isValid:
            return

        input_query = query.string.strip()

        item = Item(
            id=__prettyname__,
            icon=icon_path,
            completion=query.rawString,
            text=__prettyname__,
            actions=[]
        )

        if len(query.string) >= 3:
            repo_list = get_repos()
            for repo in repo_list:
                cleaned_query = str(input_query).replace('#', '').replace('!', '')
                if cleaned_query in repo.html_url:
                    repo_url = repo.html_url
                    if "!" in str(input_query): repo_url = repo_url + "/issues"
                    elif "#" in str(input_query): repo_url = repo_url + "/pulls"
                    # TODO: Add support for branch switching
                    results.append(Item(
                        id=__prettyname__,
                        icon=icon_path,
                        text=repo.name,
                        subtext=repo.description if repo.description else "",
                        actions=[UrlAction("Open in Github", repo_url)])
                    )
        else:
            item.subtext = "Jump to repo in Github! Enter more than 2 Characters to begin search."
            return item
    return results

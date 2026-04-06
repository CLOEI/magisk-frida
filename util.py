import re
import requests
import subprocess


# 7.5-2, 7.5-3, ... -> 7.5
def strip_revision(tag) -> str:
    return tag.split('-', 1)[0]


# gets last tag of GitHub project via releases API
def get_last_github_tag(project_name) -> str:
    releases_url = f"https://api.github.com/repos/{project_name}/releases/latest"
    r = requests.get(releases_url)
    r.raise_for_status()
    releases = r.json()
    last_release = releases["tag_name"]
    return last_release


# gets last tag of cheat-engine
def get_last_ce_tag() -> str:
    # CE releases have no binary assets but do publish release tags
    last_ce_tag = get_last_github_tag('cheat-engine/cheat-engine')
    print(f"Last cheat-engine tag: {last_ce_tag}")
    return last_ce_tag


# gets last tag of whole project
def get_last_project_tag() -> str:
    last_tag = get_last_tag([])
    print(f"Last project tag: {last_tag}")
    return last_tag


# properly sort tags (e.g. 1.11 > 1.9)
def sort_tags(tags: [str]) -> [str]:
    tags = tags.copy()
    s: str
    tags.sort(key=lambda s: list(map(int, re.split(r"[\.-]", s))))
    return tags


# gets last tag from filter
def get_last_tag(filter_args: [str]) -> str:
    tags = exec_git_command(["tag", "-l"] + filter_args).splitlines()
    last_tag = "" if len(tags) < 1 else sort_tags(tags)[-1]
    return last_tag


# executes a git command
def exec_git_command(command_with_args: [str]) -> str:
    result = subprocess.run(["git"] + command_with_args,
                            capture_output=True).stdout
    return result.decode()


# gets next tag in the form 7.5-1, 7.5-2...
def get_next_revision(current_tag: str) -> str:
    i = 1
    while True:
        new_tag = f"{current_tag}-{i}"
        if get_last_tag([new_tag]) == '':
            break
        i += 1
    return new_tag

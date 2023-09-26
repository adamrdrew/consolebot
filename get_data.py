import requests
import json


ORG_NAME = "RedHatInsights"
BASE_URL = f"https://api.github.com/orgs/{ORG_NAME}/repos"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {TOKEN}"
}

def get_all_repos(base_url, headers):
    repos = []
    while base_url:
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch repos. Status code: {response.status_code}")
        repos.extend(response.json())
        base_url = response.links.get("next", {}).get("url")  # Pagination
    return repos

def get_readme_and_history(repo, headers):
    repo_name = repo['name']
    # Fetching README
    readme_url = repo["contents_url"].replace("{+path}", "README.md")
    readme_response = requests.get(readme_url, headers=headers)
    
    if readme_response.status_code == 200:
        readme_content = readme_response.json()["content"]
    else:
        readme_content = None
    
    # Fetching Git History
    commits_url = repo["commits_url"].replace("{/sha}", "")
    commits_response = requests.get(commits_url, headers=headers)
    
    if commits_response.status_code == 200:
        commit_history = commits_response.json()
    else:
        commit_history = None
    
    return {
        "repo_name": repo_name,
        "readme_content": readme_content,
        "commit_history": commit_history
    }

repos = get_all_repos(BASE_URL, HEADERS)

data = []
for repo in repos:
    repo_data = get_readme_and_history(repo, HEADERS)
    data.append(repo_data)

with open("repos_data.json", "w") as f:
    json.dump(data, f, indent=4)
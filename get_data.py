import requests
import json

def read_token_from_file(file_path="token.txt"):
    with open(file_path, 'r') as file:
        return file.readline().strip()

TOKEN = read_token_from_file()

ORG_NAME = "RedHatInsights"
BASE_URL = f"https://api.github.com/orgs/{ORG_NAME}/repos"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {TOKEN}"
}

def get_all_repos(base_url, headers):
    repos = []
    page_num = 1
    while base_url:
        print(f"Fetching repositories from page {page_num}...")
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch repos. Status code: {response.status_code}")
        repos.extend(response.json())
        base_url = response.links.get("next", {}).get("url")  # Pagination
        page_num += 1
    print(f"Total repositories fetched: {len(repos)}")
    return repos

def get_readme_and_history(repo, headers):
    repo_name = repo['name']
    print(f"\nProcessing repository: {repo_name}")
    
    # Fetching README
    print(f"Fetching README for {repo_name}...")
    readme_url = repo["contents_url"].replace("{+path}", "README.md")
    readme_response = requests.get(readme_url, headers=headers)
    
    if readme_response.status_code == 200:
        readme_content = readme_response.json()["content"]
    else:
        print(f"Failed to fetch README for {repo_name}. Status code: {readme_response.status_code}")
        readme_content = None
    
    # Fetching Git History
    print(f"Fetching commit history for {repo_name}...")
    commits_url = repo["commits_url"].replace("{/sha}", "")
    commits_response = requests.get(commits_url, headers=headers)
    
    commit_data = []
    if commits_response.status_code == 200:
        for commit in commits_response.json()[:10]: # limit to the most recent 10 commits
            commit_info = {
                "contributor": commit["commit"]["committer"]["name"],
                "date": commit["commit"]["committer"]["date"],
                "message": commit["commit"]["message"]
            }
            commit_data.append(commit_info)
    else:
        print(f"Failed to fetch commit history for {repo_name}. Status code: {commits_response.status_code}")
    
    return {
        "repo_name": repo_name,
        "readme_content": readme_content,
        "recent_commits": commit_data
    }

repos = get_all_repos(BASE_URL, HEADERS)

data = []
for idx, repo in enumerate(repos, 1):
    print(f"\n[{idx}/{len(repos)}] Processing repo: {repo['name']}")
    repo_data = get_readme_and_history(repo, HEADERS)
    data.append(repo_data)

print("\nSaving data to repos_data.json...")
with open("data/repos_data.json", "w") as f:
    json.dump(data, f, indent=4)
print("Data saved successfully.")

import requests
import json
import time

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

def safe_request(url, headers, retries=3, backoff_factor=0.3):
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # raises an HTTPError if one occurred
            return response
        except requests.exceptions.HTTPError as http_err:
            # Handling rate limits
            if response.status_code == 429:
                print("Rate limit exceeded. Waiting...")
                time.sleep(60)  # Wait for 60 seconds before retrying
            else:
                print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Error occurred: {err}")
        time.sleep(backoff_factor)
    return None

def get_all_repos(base_url, headers):
    repos = []
    page_num = 1
    while base_url:
        print(f"Fetching repositories from page {page_num}...")
        response = safe_request(base_url, headers)
        if response:
            repos.extend(response.json())
            base_url = response.links.get("next", {}).get("url")  # Pagination
            page_num += 1
        else:
            base_url = None  # End loop if max retries reached
    print(f"Total repositories fetched: {len(repos)}")
    return repos

def get_readme_and_history(repo, headers):
    repo_name = repo['name']
    print(f"\nProcessing repository: {repo_name}")
    
    # Fetching README
    print(f"Fetching README for {repo_name}...")
    readme_url = repo["contents_url"].replace("{+path}", "README.md")
    readme_response = safe_request(readme_url, headers)
    
    if readme_response:
        readme_content = readme_response.json().get("content", None)
    else:
        readme_content = None
    
    # Fetching Git History
    print(f"Fetching commit history for {repo_name}...")
    commits_url = repo["commits_url"].replace("{/sha}", "")
    commits_response = safe_request(commits_url, headers)
    
    commit_data = []
    if commits_response:
        for commit in commits_response.json()[:10]:  # limit to the most recent 10 commits
            commit_info = {
                "contributor": commit["commit"]["committer"]["name"],
                "date": commit["commit"]["committer"]["date"],
                "message": commit["commit"]["message"]
            }
            commit_data.append(commit_info)
    
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

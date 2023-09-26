import requests
import json
import BeautifulSoup

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

def has_readme(repo, headers):
    """Checks if a repository has a README.md file."""
    readme_url = repo["contents_url"].replace("{+path}", "README.md")
    readme_response = requests.head(readme_url, headers=headers)  # Using HEAD request to check existence
    return readme_response.status_code == 200


def get_all_repos(base_url, headers):
    repos = []
    page_num = 1
    while base_url:
        print(f"Fetching repositories from page {page_num}...")
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch repos. Status code: {response.status_code}")
        repos.extend([r for r in response.json() if not r['name'].endswith('-build')])  # Skip repos ending in '-build'
        base_url = response.links.get("next", {}).get("url")  # Pagination
        page_num += 1
    print(f"Total repositories fetched: {len(repos)}")
    return repos

def get_commit_history(commits_url, headers, max_commits=100):
    commit_data = []
    commit_count = 0

    while commits_url and commit_count < max_commits:
        commits_response = requests.get(commits_url, headers=headers)
        
        if commits_response.status_code == 200:
            for commit in commits_response.json():
                if commit_count >= max_commits:
                    break

                commit_info = {
                    "contributor": commit["commit"]["committer"]["name"],
                    "date": commit["commit"]["committer"]["date"],
                    "message": commit["commit"]["message"]
                }

                commit_data.append(commit_info)
                commit_count += 1

            commits_url = commits_response.links.get("next", {}).get("url")  # Pagination for commits
        else:
            print(f"Failed to fetch commits. Status code: {commits_response.status_code}")
            break

    return commit_data


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
    commit_data = get_commit_history(commits_url, headers)
    
    # Fetching Languages
    languages_url = repo["languages_url"]
    lang_response = requests.get(languages_url, headers=headers)
    languages = lang_response.json() if lang_response.status_code == 200 else {}

    # Fetching Top Contributors
    contributors_url = repo["contributors_url"] + "?per_page=3"
    contributors_response = requests.get(contributors_url, headers=headers)
    top_contributors = [contributor["login"] for contributor in contributors_response.json()] if contributors_response.status_code == 200 else []

    return {
        "repo_name": repo_name,
        "readme_content": readme_content,
        "recent_commits": commit_data,
        "languages": languages,
        "top_contributors": top_contributors
    }

repos = get_all_repos(BASE_URL, HEADERS)

data = []
for idx, repo in enumerate(repos, 1):
    print(f"\n[{idx}/{len(repos)}] Processing repo: {repo['name']}")
    
    # Check for README existence
    if not has_readme(repo, HEADERS):
        print(f"No README found for {repo['name']}. Skipping...")
        continue

    repo_data = get_readme_and_history(repo, HEADERS)
    data.append(repo_data)


print("\nSaving data to repos_data.json...")
with open("data/repos_data.json", "w") as f:
    json.dump(data, f, indent=4)
print("Data saved successfully.")

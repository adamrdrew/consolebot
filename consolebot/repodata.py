import requests
import json
import base64
import re
from docutils import nodes
from docutils.core import publish_doctree

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

def extract_plain_text_from_rst(rst_content):
    """Extract plain text from reStructuredText (RST) content."""
    
    # Parse the RST content into a document tree
    doctree = publish_doctree(rst_content)

    # Define a visitor class to extract text from the document tree
    class TextVisitor(nodes.SparseNodeVisitor):
        def __init__(self, document):
            nodes.SparseNodeVisitor.__init__(self, document)
            self.text_list = []
        
        def default_visit(self, node):
            if isinstance(node, nodes.Text):
                self.text_list.append(node.astext())
    
    # Apply the visitor to the document tree
    visitor = TextVisitor(doctree)
    doctree.walk(visitor)
    
    # Join the text and return
    return '\n'.join(visitor.text_list).strip()

def gather_repo_data(repo, headers):
    """Gather data for a single repo."""
    
    # Check for README existence
    readme_filename = has_readme(repo, headers)
    if not readme_filename:
        print(f"No README found for {repo['name']}. Skipping...")
        return None
    
    # Get README content
    readme_content = get_readme_content(repo, headers)
    if not readme_content:
        print(f"Failed to fetch README content for {repo['name']} after max retries.")
        return None
    
    languages = get_repo_languages(repo['languages_url'], headers)
    # Get Commit History
    commits = get_commit_history(repo['commits_url'], headers)
    recent_commits = [commit["message"] for commit in commits[:3]]  # Taking only the recent 3 commits
    
    # Get Contributors from commit history
    contributors = list(set([commit["contributor"] for commit in commits]))
    
    # Build the JSON object
    repo_data = {
        repo['name']: {
            "title": repo['name'],
            "description": repo['description'],
            "readme": readme_content,
            "contributors": contributors,
            "recent_commits": recent_commits,
            "url": repo['html_url'],
            "languages": languages,
            
        }
    }

    return repo_data


def get_repo_contributors(repo, headers):
    """Returns the list of contributors for a repo."""
    contributors_url = repo["contributors_url"]
    response = safe_request(requests.get, contributors_url, headers)
    if not response or response.status_code != 200:
        return []
    return [contributor['login'] for contributor in response.json()]

def safe_request(request_func, url, headers, max_retries=3):
    """
    Performs a safe request, retrying in case of timeouts.
    
    Args:
        request_func: A function like requests.get or requests.head.
        url (str): The URL to fetch.
        headers (dict): The headers for the request.
        max_retries (int): The number of retries.
        
    Returns:
        The response object or None in case of failures after retries.
    """
    for _ in range(max_retries):
        try:
            response = request_func(url, headers=headers, timeout=10)  # Setting a timeout of 10 seconds
            if response.status_code == 200:
                return response
            print(f"Failed request for URL {url}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching {url}. Error: {e}")
    return None

def has_readme(repo, headers):
    """Checks if a repository has a README file and returns its format."""
    formats = ["md", "adoc", "rst", "txt"]

    root_files = get_repo_root_files(repo, headers)
    # Finding any readme file irrespective of its case and format
    for file in root_files:
        if file.lower() == "readme.md" or file.lower() == "readme.adoc" or file.lower() == "readme.rst" or file.lower() == "readme.txt":
            return file  # Return the exact filename of the found README file


    return None




def get_all_repos(base_url, headers):
    repos = []
    page_num = 1
    while base_url:
        print(f"Fetching repositories from page {page_num}...")
        response = safe_request(requests.get, base_url, headers)
        if not response:
            raise ValueError(f"Failed to fetch repos after max retries. Aborting.")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch repos. Status code: {response.status_code}")
        repos.extend([r for r in response.json() if not r['name'].endswith('-build')])  # Skip repos ending in '-build'
        base_url = response.links.get("next", {}).get("url")  # Pagination
        page_num += 1
    print(f"Total repositories fetched: {len(repos)}")
    return repos

def get_repo_languages(languages_url, headers):
    """Fetch languages for a repo."""
    response = requests.get(languages_url, headers=headers)
    if response.status_code == 200:
        return list(response.json().keys())
    else:
        print(f"Failed request for URL {languages_url}. Status code: {response.status_code}")
        return []

def get_commit_history(commits_url, headers, max_commits=100):
    commit_data = []
    commit_count = 0
    commits_url = commits_url.split("{")[0]
    while commits_url and commit_count < max_commits:
        commits_response = safe_request(requests.get, commits_url, headers)
        if not commits_response:
            break
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

def extract_plain_text_from_adoc(adoc_content):
    """Extract plain English text from AsciiDoc content by removing common markup."""
    
    # Remove inline styles: *bold*, _italic_, +monospace+, etc.
    adoc_content = re.sub(r'[\*\_\+\^\~]', '', adoc_content)
    
    # Remove links: link:[text], http://example.com[text], etc.
    adoc_content = re.sub(r'link:\[.*?\]', '', adoc_content)
    adoc_content = re.sub(r'http[s]?://\S+\[.*?\]', '', adoc_content)
    
    # Remove image tags: image::path[Alt Text]
    adoc_content = re.sub(r'image::.*?\[.*?\]', '', adoc_content)
    
    # Remove source code blocks
    adoc_content = re.sub(r'\[source,.*?\]\n----.*?----', '', adoc_content, flags=re.DOTALL)
    
    # Remove other blocks: NOTE, TIP, WARNING, etc.
    adoc_content = re.sub(r'^NOTE:.*?$', '', adoc_content, flags=re.MULTILINE)
    adoc_content = re.sub(r'^TIP:.*?$', '', adoc_content, flags=re.MULTILINE)
    adoc_content = re.sub(r'^WARNING:.*?$', '', adoc_content, flags=re.MULTILINE)
    adoc_content = re.sub(r'^IMPORTANT:.*?$', '', adoc_content, flags=re.MULTILINE)
    
    # Remove block quotes
    adoc_content = re.sub(r'^____.*?____', '', adoc_content, flags=re.DOTALL)
    
    # Remove headers: == Header, === Sub-header, etc.
    adoc_content = re.sub(r'^=+ .*?$', '', adoc_content, flags=re.MULTILINE)
    
    # Remove lists: . Item, * Item, etc.
    adoc_content = re.sub(r'^\. .*?$', '', adoc_content, flags=re.MULTILINE)
    adoc_content = re.sub(r'^\* .*?$', '', adoc_content, flags=re.MULTILINE)
    
    # Remove comments
    adoc_content = re.sub(r'^//.*?$', '', adoc_content, flags=re.MULTILINE)

    # Additional cleanups, like consecutive newlines
    adoc_content = re.sub(r'\n{3,}', '\n\n', adoc_content)
    
    return adoc_content.strip()

def get_repo_root_files(repo, headers):
    """Returns the list of files in the root directory of a repo."""
    contents_url = repo["contents_url"].replace("{+path}", "")
    response = safe_request(requests.get, contents_url, headers)
    if not response or response.status_code != 200:
        return []
    return [item['name'] for item in response.json()]


def get_readme_content(repo, headers):
    repo_name = repo['name']
    print(f"\nProcessing repository: {repo_name}")

    # Get the exact README filename
    readme_filename = has_readme(repo, headers)
    if not readme_filename:
        print(f"No README found for {repo['name']}. Skipping...")
        return None

    print(f"Fetching {readme_filename} for {repo_name}...")
    readme_url = repo["contents_url"].replace("{+path}", readme_filename)
    readme_response = safe_request(requests.get, readme_url, headers)
    if not readme_response:
        print(f"Failed to fetch {readme_filename} for {repo_name} after max retries.")
        return None
    
    if readme_response.status_code == 200:
        readme_content_encoded = readme_response.json()["content"]
        readme_content_decoded = base64.b64decode(readme_content_encoded).decode('utf-8')
        
        # Convert to markdown or plain text depending on format
        if readme_filename.endswith('.adoc'):
            readme_content_decoded = extract_plain_text_from_adoc(readme_content_decoded)
        elif readme_filename.endswith('.rst'):
            readme_content_decoded = extract_plain_text_from_rst(readme_content_decoded)
        # For .txt, it's plain text, and for .md, it's already markdown, so no conversions are needed.
    else:
        print(f"Failed to fetch {readme_filename} for {repo_name}. Status code: {readme_response.status_code}")
        readme_content_decoded = None
    
    return readme_content_decoded

def get():
    repos = get_all_repos(BASE_URL, HEADERS)
    data = {}
    try_again_list = []

    for idx, repo in enumerate(repos, 1):
        print(f"\n[{idx}/{len(repos)}] Processing repo: {repo['name']}")
        repo_data = gather_repo_data(repo, HEADERS)
        
        if repo_data:
            data.update(repo_data)
        else:
            try_again_list.append(repo)

    # Retry for repos in the try again list
    for idx, repo in enumerate(try_again_list, 1):
        print(f"\nRetry [{idx}/{len(try_again_list)}] Processing repo: {repo['name']}")
        repo_data = gather_repo_data(repo, HEADERS)
        if repo_data:
            data.update(repo_data)

    print("\nSaving data to repos_data.json...")
    with open("data/repos_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Data saved successfully.")


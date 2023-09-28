import requests
import json
import base64
import re
from docutils import nodes
from docutils.core import publish_doctree
import os
import datetime

class GithubData:
    
    ORG_NAME = "RedHatInsights"
    BASE_URL = f"https://api.github.com/orgs/{ORG_NAME}/repos"
    DATA_PATH = os.path.expanduser('~/.config/consolebot/repos.json')
    TOKEN_PATH = os.path.expanduser('~/.config/consolebot/token')
    CACHE_DURATION = datetime.timedelta(days=30)
    _formatted_repos_cache = None

    @classmethod
    def get_formatted_repos(cls):
        if cls._formatted_repos_cache:  # Return memoized results if exists
            return cls._formatted_repos_cache
        
        repos_data = cls.get_repos()
        repos = repos_data.get('repos', [])

        # 2. Formatting:
        formatted_repos = {}
        for repo in repos:
            repo_name = repo['name']
            formatted_repos[repo_name] = repo
        cls._formatted_repos_cache = formatted_repos  # Store the result for memoization
        return formatted_repos

    @classmethod
    def extract_plain_text_from_adoc(cls, adoc_content):
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

    @classmethod
    def extract_plain_text_from_rst(cls, rst_content):
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

    @classmethod
    def get_repo_root_files(cls, repo):
        headers = cls.get_headers()
        """Returns the list of files in the root directory of a repo."""
        contents_url = repo["contents_url"].replace("{+path}", "")
        response = cls.safe_request(requests.get, contents_url, headers)
        if not response or response.status_code != 200:
            return []
        return [item['name'] for item in response.json()]

    @classmethod
    def get_readme_content(cls, repo):
        headers = cls.get_headers()
        repo_name = repo['name']
        print(f"\nProcessing repository: {repo_name}")

        # Get the exact README filename
        readme_filename = cls.has_readme(repo, headers)
        if not readme_filename:
            print(f"No README found for {repo['name']}. Skipping...")
            return None

        print(f"Fetching {readme_filename} for {repo_name}...")
        readme_url = repo["contents_url"].replace("{+path}", readme_filename)
        readme_response = cls._safe_request(requests.get, readme_url, headers)
        if not readme_response:
            print(f"Failed to fetch {readme_filename} for {repo_name} after max retries.")
            return None
        
        if readme_response.status_code == 200:
            readme_content_encoded = readme_response.json()["content"]
            readme_content_decoded = base64.b64decode(readme_content_encoded).decode('utf-8')
            
            # Convert to markdown or plain text depending on format
            if readme_filename.endswith('.adoc'):
                readme_content_decoded = cls.extract_plain_text_from_adoc(readme_content_decoded)
            elif readme_filename.endswith('.rst'):
                readme_content_decoded = cls.extract_plain_text_from_rst(readme_content_decoded)
            # For .txt, it's plain text, and for .md, it's already markdown, so no conversions are needed.
        else:
            print(f"Failed to fetch {readme_filename} for {repo_name}. Status code: {readme_response.status_code}")
            readme_content_decoded = None
        
        return readme_content_decoded

    @classmethod
    def get_repo_contributors(cls, repo):
        headers = cls.get_headers()
        """Returns the list of contributors for a repo."""
        contributors_url = repo["contributors_url"]
        response = cls._safe_request(requests.get, contributors_url, headers)
        if not response or response.status_code != 200:
            return []
        return [contributor['login'] for contributor in response.json()]

    @classmethod
    def has_readme(cls, repo):
        """Checks if a repository has a README file and returns its format."""
        formats = ["md", "adoc", "rst", "txt"]

        root_files = cls.get_repo_root_files(repo)
        # Finding any readme file irrespective of its case and format
        for file in root_files:
            if file.lower() == "readme.md" or file.lower() == "readme.adoc" or file.lower() == "readme.rst" or file.lower() == "readme.txt":
                return file  # Return the exact filename of the found README file

        return None

    @classmethod
    def get_repo_languages(cls, repo):
        languages_url = repo["languages_url"]
        headers = cls.get_headers()
        """Fetch languages for a repo."""
        response = requests.get(languages_url, headers=headers)
        if response.status_code == 200:
            return list(response.json().keys())
        else:
            print(f"Failed request for URL {languages_url}. Status code: {response.status_code}")
            return []

    @classmethod
    def get_commit_history(cls, commits_url, max_commits=100):
        headers = cls.get_headers()
        commit_data = []
        commit_count = 0
        commits_url = commits_url.split("{")[0]
        while commits_url and commit_count < max_commits:
            commits_response = cls._safe_request(requests.get, commits_url, headers)
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

    @classmethod
    def get_headers(cls):
        token = cls.get_token()
        if not token:
            print("Please obtain a personal access token and place it in ~/.config/consolebot/token")
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        return headers


    @classmethod
    def get_repos(cls):
        headers = cls.get_headers()
        
        repos = cls._load_cache()
        if not repos:
            repos = cls._fetch_and_cache_repos(headers)
            print("Data fetched from GitHub.")
        return repos

    @classmethod
    def get_token(cls):
        if os.path.exists(cls.TOKEN_PATH):
            with open(cls.TOKEN_PATH, 'r') as file:
                return file.read().strip()
        return None

    @classmethod
    def _load_cache(cls):
        if os.path.exists(cls.DATA_PATH):
            with open(cls.DATA_PATH, 'r') as file:
                cache = json.load(file)
                last_updated = datetime.datetime.fromisoformat(cache.get('timestamp', ''))
                if datetime.datetime.now() - last_updated > cls.CACHE_DURATION:
                    print("Cache is old. Consider refreshing the data.")
                return cache.get('repos', [])
        return []

    @classmethod
    def _fetch_and_cache_repos(cls, headers):
        repos = cls._get_all_repos(cls.BASE_URL, headers)
        cache = {
            'repos': repos,
            'timestamp': datetime.datetime.now().isoformat()
        }
        with open(cls.DATA_PATH, 'w') as file:
            json.dump(cache, file)
        return repos

    @classmethod
    def _get_all_repos(cls, base_url, headers):
        repos = []
        page_num = 1
        while base_url:
            print(f"Fetching repositories from page {page_num}...")
            response = cls._safe_request(requests.get, base_url, headers=headers)
            if not response:
                raise ValueError(f"Failed to fetch repos after max retries. Aborting.")
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch repos. Status code: {response.status_code}")
            repos.extend([r for r in response.json() if not r['name'].endswith('-build')])  # Skip repos ending in '-build'
            base_url = response.links.get("next", {}).get("url")  # Pagination
            page_num += 1
        print(f"Total repositories fetched: {len(repos)}")
        return repos

    @staticmethod
    def _safe_request(request_func, url, headers, max_retries=3):
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

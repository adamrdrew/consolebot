import json
from bs4 import BeautifulSoup

def remove_markdown(content):
    """Convert markdown to plain text"""
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text()

def process_repo_data(file_path="repos_data.json"):
    with open(file_path, "r") as f:
        data = json.load(f)

    knowledge_base = ""
    commit_data = {}

    for repo in data:
        if repo["readme_content"]:
            repo_name = repo["repo_name"]
            readme_content = remove_markdown(repo["readme_content"])
            
            # Add the processed README content to the knowledge base
            knowledge_base += f"Repository: {repo_name}\n\n{readme_content}\n\n"

            # Process and store commit information for each repository
            contributors = set()
            commit_messages = []

            for commit in repo["recent_commits"]:
                contributors.add(commit["contributor"])
                commit_messages.append(commit["message"])

            commit_data[repo_name] = {
                "contributors": list(contributors),
                "recent_commits": commit_messages
            }

    return knowledge_base, commit_data

knowledge_base, commit_data = process_repo_data()

# Save the knowledge base to a text file for training
with open("data/knowledge_base.txt", "w") as f:
    f.write(knowledge_base)

# Save the commit data as JSON for later reference
with open("data/commit_data.json", "w") as f:
    json.dump(commit_data, f, indent=4)

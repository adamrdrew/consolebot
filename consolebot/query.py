import itertools
import spacy
import json
from summarizer import Summarizer
from fuzzywuzzy import process
import markdown
from bs4 import BeautifulSoup
from rich import print
from rich.text import Text
from fuzzywuzzy import fuzz
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk.tokenize import word_tokenize
import re
import warnings
import os
from consolebot.githubdata import GithubData 

warnings.simplefilter(action='ignore', category=FutureWarning)


# Download necessary NLTK data
import nltk
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

stop_words = set(stopwords.words('english'))

class RepoNotFoundException(Exception):
    pass

nlp = spacy.load("en_core_web_md")

cached_github_data = GithubData.get_repos()

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

def get_wordnet_pos(treebank_tag):
    """Map treebank pos tag to first character used by WordNetLemmatizer"""
    tag = treebank_tag[0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def preprocess_text(text, remove_stopwords=True):
    # Tokenize
    tokens = nltk.word_tokenize(text)
    
    # Lemmatize
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Remove stopwords
    if remove_stopwords:
        lemmatized_tokens = [token for token in lemmatized_tokens if token.lower() not in stopwords.words('english')]
    
    # Joining tokens
    processed_text = ' '.join(lemmatized_tokens)
    return processed_text


def determine_intent(query, repo_name, intents):
    query = query.replace(repo_name, '').strip().lower()

    best_match_score = -1
    detected_intent = None

    for intent, phrases in intents.items():
        for phrase in phrases:
            score = process.extractOne(query, [phrase])[1]
            if score > best_match_score:
                best_match_score = score
                detected_intent = intent

    # Setting a threshold, below which the intent is considered not detected (you can adjust as needed)
    if best_match_score < 80:  # Adjust the threshold based on your observation
        return None
    return detected_intent



def get_summary(repo_name):
    for repo_key, repo in cached_github_data.items():
        if repo_key == repo_name:
            readme = GithubData.get_readme(repo)
            if not readme:
                return "No summary available."

            html_content = markdown.markdown(readme)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted tags
            for tag in soup.find_all(['img']):
                tag.decompose()

            plain_text = ' '.join(soup.stripped_strings)

            # Remove unwanted patterns or strings
            for pattern in [':note-caption:', ':informationsource:', 'image:', 'adoc[Learn More]']:
                plain_text = plain_text.replace(pattern, '')

            # Replace multiple newlines/spaces with a single space
            plain_text = re.sub(r'\s+', ' ', plain_text)
            
            # Direct Extraction of first N sentences
            sentences = plain_text.split('.')
            intro_text = '. '.join(sentences[:3]).strip()  # Taking the first 5 sentences as an example

            # Now, summarize this introduction
            description = repo.get("description") or ""
            model = Summarizer()
            nlp_summary = model(intro_text, num_sentences=3)  # Adjust the count as needed
            nlp_summary = description + "\n" + nlp_summary

            return nlp_summary
    return "Repository not found."


def get_recent_activity(repo_name, num_commits=5):  # default to showing the last 5 commits
    for repo_key, repo in cached_github_data.items():
        if repo_key == repo_name:
            commits = GithubData.get_commits(repo)
            # If there are fewer commits than the default number, show them all
            return "\n".join(commits[:num_commits]) if commits else "No recent commits found."
    return "Repository not found."


def get_contributors(repo_name):
    for repo_key, repo in cached_github_data.items():
        if repo_key == repo_name:
            contributors = [name for name in GithubData.get_repo_contributors(repo) if name != "Github"]
            return ", ".join(sorted(contributors))
    return "Repository not found."


def get_language(repo_name):
    for repo_key, repo in cached_github_data.items():
        if repo_key == repo_name:
            return ', '.join(GithubData.get_repo_languages(repo))
    return "Repository not found."

def generate_combinations(query):
    query_words = [word for word in query.split() if word not in stop_words]
    combinations = []

    for i in range(2, len(query_words) + 1):
        for combo in itertools.combinations(query_words, i):
            combinations.append("-".join(combo))

    return combinations


def disambiguate_repo_name(top_matches):
    print("Multiple repositories matched your query:")
    for idx, (match_name, match_score) in enumerate(top_matches, 1):
        print(f"{idx}. {match_name} ({match_score}%)")
    
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        choice = input("Please select the correct repository by number: ")
        try:
            selected_repo = top_matches[int(choice)-1][0]
            return selected_repo
        except (ValueError, IndexError):
            attempts += 1
            if attempts == max_attempts:
                print("Invalid choices exceeded. Defaulting to the first option.")
                return top_matches[0][0]
            else:
                print(f"Invalid choice. You have {max_attempts - attempts} attempts left. Please select a valid number from the list.")


def determine_repo_name(query, disambiguator=disambiguate_repo_name):
    repo_name = None
    intent = None
    
    # Extract repo names for fuzzy matching
    repo_names = [repo_key for repo_key, repo in cached_github_data.items()]

    query_combinations = generate_combinations(query)
    # Check for multi-word exact matches first
    multi_word_matches = [name for name in repo_names if name in query_combinations]

    if multi_word_matches:
        repo_name = max(multi_word_matches, key=len)  # choose the longest match, assuming it's more specific
    else:
        # Check for single-word exact matches
        query_words = set(query.split())
        single_word_matches = query_words.intersection(repo_names)
        if single_word_matches:
            repo_name = single_word_matches.pop()  # take any exact match (if multiple, just take one)
    
    if not repo_name:
        # Find the best fuzzy match for the repo name in the query
        matches = process.extract(query, repo_names, limit=10)
        matches = sorted(matches, key=lambda x: (-x[1], len(x[0])))
        
        # Check the top matches for disambiguation
        top_matches = matches[:3]  # Get top 3 matches
        best_match, best_match_score = top_matches[0]

        if len(top_matches) > 1 and (best_match_score - top_matches[1][1]) < 10:  # Threshold of 10 can be adjusted
            repo_name = disambiguator(top_matches)
        elif best_match_score >= 70:
            repo_name = best_match
        else:
            raise RepoNotFoundException(f"Could not identify a repository from the query: '{query}'")
    
    # Determine intent
    return repo_name

def run(query):
    # Define intents and their key phrases
    intents = {
        "summary": ["summary", "describe", "explain", "what is", "tell me about", "details", "overview", "tell me a bit about", "does do"],
        "contributors": ["who works", "works", "contributors", "team members", "developers", "maintainers", "people", "team"],
        "language": ["language", "written in", "coding language", "programmed in", "developed in", "coded in", "developed in"],
        "recent_activity": ["recent", "recently", "new", "changes", "updates",  "happening", "going on", "changed"]
    }
    intent = None
    repo_name = None
    try:
        repo_name = determine_repo_name(query)
        intent = determine_intent(query, repo_name, intents)
        # rest of your code
    except RepoNotFoundException as e:
        print(e)  # or print(str(e)) for just the message without the traceback
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

    response_text = Text()
    
    if isinstance(intent, str):
        response_text.append("Intent: ", style="none")
        response_text.append(intent, style="bold cyan")
    else:
        response_text.append("Intent not identified.", style="bold red")

    if isinstance(repo_name, str):
        response_text.append("\nRepository: ", style="none")
        response_text.append(repo_name, style="bold green")
    else:
        response_text.append("\nRepository not identified.", style="bold red")

    if intent == "summary":
        summary = get_summary(repo_name)
        response_text.append("\nSummary: ", style="none")
        response_text.append(summary)
    elif intent == "contributors":
        contributors = get_contributors(repo_name)
        response_text.append("\n" + contributors)
    elif intent == "language":
        language = get_language(repo_name)
        response_text.append("\n" + language)
    elif intent == "recent_activity":
        recent_activity = get_recent_activity(repo_name)
        response_text.append("\n" + recent_activity)

    print(response_text)


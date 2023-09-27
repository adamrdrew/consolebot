import base64
import spacy
import json
from summarizer import summarize
from fuzzywuzzy import process
import markdown
from bs4 import BeautifulSoup
from rich import print
from rich.panel import Panel
from rich.text import Text
from fuzzywuzzy import fuzz
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk.tokenize import word_tokenize
import re
import click

# Download necessary NLTK data
import nltk
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Define intents and their key phrases
intents = {
    "summary": ["summary", "describe", "explain", "what is", "tell me about", "details", "overview", "tell me a bit about", "does do"],
    "contributors": ["who works", "contributors", "team members", "developers", "maintainers", "people"],
    "language": ["language", "written in", "coding language", "programmed in", "developed in"]
}


class RepoNotFoundException(Exception):
    pass



nlp = spacy.load("en_core_web_sm")

# Load data from JSON file
with open('data/repos_data.json', 'r') as file:
    data = json.load(file)

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


def determine_intent(query, repo_name):

    query = query.replace(repo_name, '').strip()

    processed_query = preprocess_text(query)

    # Using fuzzy matching to find the closest intent
    max_score = 0
    detected_intent = None

    for intent, phrases in intents.items():
        for phrase in phrases:
            score = fuzz.ratio(processed_query, preprocess_text(phrase))
            #print(f"Comparing '{processed_query}' to '{preprocess_text(phrase)}' results in score: {score}")
            if score > max_score:
                max_score = score
                detected_intent = intent

    # Setting a threshold, below which the intent is considered not detected (you can adjust as needed)
    if max_score < 60: 
        return None
    return detected_intent

def get_summary(repo_name):
    for repo_key, repo in data.items():
        if repo_key == repo_name:
            html_content = markdown.markdown(repo['readme'])
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
            
            # Top-N Sentences
            sentences = plain_text.split('.')
            top_n_sentences = '. '.join(sentences[:3]).strip()  # Taking the first 3 sentences

            # For Keyword Weighting
            # Define your keywords (can be expanded as needed)
            keywords = ["introduction", "overview", "purpose", "use", "functionality", "goal"]
            
            weighted_sentences = [sentence for sentence in sentences if any(keyword in sentence for keyword in keywords)]
            keyword_weighted_summary = '. '.join(weighted_sentences[:3]).strip()  # Take the first 3 keyword-rich sentences
            
            # Decide which one to return based on some criteria, or combine both.
            # Here, I'm combining both:
            combined_summary = top_n_sentences + '. ' + keyword_weighted_summary

            return combined_summary if repo['readme'] else "No summary available."
    return "Repository not found."

def get_contributors(repo_name):
    for repo_key, repo in data.items():
        if repo_key == repo_name:
            return ", ".join(repo.get('contributors', []))
    return "Repository not found."

def get_language(repo_name):
    for repo_key, repo in data.items():
        if repo_key == repo_name:
            return ', '.join(repo.get('languages', ['Unknown']))
    return "Repository not found."

def extract_intent_and_repo_name(query):
    repo_name = None
    intent = None
    
    # Extract repo names for fuzzy matching
    repo_names = [repo_key for repo_key, repo in data.items()]
    
    # Find the best fuzzy match for the repo name in the query
    matches = process.extract(query, repo_names, limit=10)
    matches = sorted(matches, key=lambda x: (-x[1], len(x[0])))
    best_match, match_score = matches[0]
    
    if match_score >= 70:  # You can adjust this threshold based on your requirements
        repo_name = best_match
    else:
        raise RepoNotFoundException(f"Could not identify a repository from the query: '{query}'")

    # Determine intent
    intent = determine_intent(query, repo_name)

    return intent, repo_name

def run_query(query):
    try:
        intent, repo_name = extract_intent_and_repo_name(query)
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

    print(response_text)


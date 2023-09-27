import json
import base64
from transformers import BertTokenizer, BertModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Data Preprocessing
def decode_base64(data):
    return base64.b64decode(data).decode('utf-8')

def preprocess_data(file_path):
    with open(file_path, 'r') as f:
        repos_data = json.load(f)
    for repo in repos_data:
        if repo['readme_content']:
            repo['readme_content'] = decode_base64(repo['readme_content'])
    return repos_data

def generate_embeddings(repos_data):
    # Load pre-trained BERT model and tokenizer
    model_name = 'bert-base-uncased'
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    
    # Store embeddings for each repo
    repo_embeddings = {}

    for repo in repos_data:
        content = repo['readme_content']

        if not content:
            continue
        
        # Tokenize and convert to tensor
        inputs = tokenizer.encode_plus(content, return_tensors="pt", truncation=True, padding='max_length', max_length=512)
        
        # Generate embeddings
        with torch.no_grad():
            outputs = model(**inputs)
        # Use mean of last hidden state as embedding
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
        
        repo_embeddings[repo['repo_name']] = embedding

    return repo_embeddings

def find_similar_repo(query, embeddings):
    model_name = 'bert-base-uncased'
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    
    # Convert query to embedding
    inputs = tokenizer.encode_plus(query, return_tensors="pt", truncation=True, padding='max_length', max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    query_embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    
    # Calculate cosine similarities between the query and all repo embeddings
    similarities = {}  # <-- Define similarities here
    for repo_name, repo_embedding in embeddings.items():
        cosine_sim = cosine_similarity([query_embedding], [repo_embedding])[0][0]
        similarities[repo_name] = cosine_sim

    # Return the repo with the highest similarity
    return max(similarities, key=similarities.get)


# Usage:
repos_data = preprocess_data('data/repos_data.json')
embeddings = generate_embeddings(repos_data)

query = "what repos do peter savage work on?"
most_similar_repo = find_similar_repo(query, embeddings)
print(f"The most similar repo to the query '{query}' is: {most_similar_repo}")


from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load the fine-tuned model and tokenizer
MODEL_PATH = "./custom_gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)

# Function to generate a response to a query
def generate_response(query, max_length=150, temperature=1.0):
    """
    Generate a response to a given query using the model.

    Parameters:
    - query (str): The input query.
    - max_length (int): The maximum length of the generated response.
    - temperature (float): Sampling temperature. Higher values make the output more random.

    Returns:
    - response (str): The generated response.
    """
    
    # Tokenize the query and generate response ids
    input_ids = tokenizer.encode(query, return_tensors="pt")
    output_ids = model.generate(input_ids, max_length=max_length, temperature=temperature)

    # Decode the response ids to get the response text
    response = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    return response

# Test the function
query = "who is pete savage?"
response = generate_response(query)
print(response)

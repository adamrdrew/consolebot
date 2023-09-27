import json
import base64
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling, TrainingArguments, Trainer

# Function to decode base64 encoded data
def decode_base64(data):
    return base64.b64decode(data).decode('utf-8')

# Preprocess data from JSON file
def preprocess_data(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        repos_data = json.load(file)

    repo_info_list = []

    for repo in repos_data:
        repo_info = "Repo Name: " + repo['repo_name'] + "\n"
        
        if 'readme_content' in repo and repo['readme_content']:
            repo_info += "README Content:\n" + decode_base64(repo['readme_content']) + "\n"
        
        if 'languages' in repo:
            repo_info += "Languages: " + ', '.join([k for k in repo['languages']]) + "\n"
        
        if 'top_contributors' in repo:
            repo_info += "Top Contributors: " + ', '.join(repo['top_contributors']) + "\n"

        repo_info_list.append(repo_info)

    return "\n".join(repo_info_list)

# Preprocess and save the data
data = preprocess_data('data/repos_data.json')
with open("temp_training_data.txt", "w", encoding="utf-8") as temp_file:
    temp_file.write(data)

# Load pretrained model and tokenizer
MODEL_NAME = "gpt2-medium"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)

# Create training dataset
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path="temp_training_data.txt",
    block_size=256
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Define training arguments
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    num_train_epochs=3,
    logging_dir="./logs",
    logging_steps=50,
    save_steps=100,
    output_dir="./results",
    overwrite_output_dir=True,
    save_total_limit=3
)

trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset
)

# Fine-tune the model
trainer.train()

# Save the model and tokenizer
model.save_pretrained("./custom_gpt2")
tokenizer.save_pretrained("./custom_gpt2")

# Clean up the temporary file
import os
os.remove("temp_training_data.txt")

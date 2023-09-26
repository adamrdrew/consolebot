from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling, TrainingArguments, Trainer

# Load pretrained model and tokenizer
MODEL_NAME = "gpt2-medium"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)

# Preprocess dataset
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path="data/knowledge_base.txt",
    block_size=256  # Increased block size for more context
)
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Define training arguments
training_args = TrainingArguments(
    per_device_train_batch_size=2,  # Adjust as needed
    num_train_epochs=3,  # Increase epochs for more iterations
    logging_dir="./logs",
    logging_steps=50,  # Adjust logging frequency
    save_steps=100,
    output_dir="./results",
    overwrite_output_dir=True,
    save_total_limit=3  # Save the latest 3 models for checkpoints
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

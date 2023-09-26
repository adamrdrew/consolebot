from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling, TrainingArguments, Trainer

# Load pretrained model and tokenizer
MODEL_NAME = "gpt2-medium"  # or "gpt2-small"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)

# Preprocess dataset
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path="data/knowledge_base.txt",
    block_size=128
)
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Define training arguments and set up Trainer
training_args = TrainingArguments(
    per_device_train_batch_size=4,  # adjust batch size based on your GPU memory
    num_train_epochs=1,  # number of training epochs
    logging_dir="./logs",
    logging_steps=10,
    save_steps=10,
    output_dir="./results",
    overwrite_output_dir=True,
    save_total_limit=2
)

trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset
)

# Fine-tune
trainer.train()

# Save
model.save_pretrained("./custom_gpt2")
tokenizer.save_pretrained("./custom_gpt2")

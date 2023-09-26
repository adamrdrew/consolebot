from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

model_name = "microsoft/DialoGPT-medium"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

def chat():
    print("Chatbot: Hi! Type 'exit' to end the chat.")
    user_input = ""
    while user_input != "exit":
        user_input = input("You: ")
        if user_input == "exit":
            break

        input_ids = tokenizer.encode(user_input, return_tensors="pt")
        attention_mask = torch.ones_like(input_ids)
        
        output = model.generate(
            input_ids, 
            attention_mask=attention_mask, 
            max_length=100, 
            no_repeat_ngram_size=2,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )

        # Skip user input in response
        response = tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)
        print(f"Chatbot: {response}")

chat()

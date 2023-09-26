from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import warnings

# Suppress the padding warning
warnings.filterwarnings("ignore", category=UserWarning)

model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
model = AutoModelForCausalLM.from_pretrained(model_name)

def chat():
    for step in range(5):
        # take user input
        text = input(">> You:")

        # encode the input and add end of string token
        input_ids = tokenizer.encode(text + tokenizer.eos_token, return_tensors="pt")

        # set initial chat history to user input if first step, else concatenate
        chat_history_ids = input_ids if step == 0 else torch.cat([chat_history_ids, input_ids], dim=-1)

        # generate a bot response
        chat_history_ids = model.generate(
            chat_history_ids,
            max_length=1000,
            do_sample=True,
            top_p=0.90,
            top_k=50,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )

        # print the output
        output = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
        print(f"DialoGPT: {output}")

chat()

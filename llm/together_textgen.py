from langchain_together import Together
import os
from dotenv import load_dotenv

load_dotenv()



# initialize the llm
language_model = Together(
    model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
    temperature=0.7,
    max_tokens=1028,
    top_k=1,
)


def text_generator(user_prompt, context_prompt=""):
    # combine the context prompt and user prompt, and invoke the model
    return language_model.invoke(context_prompt + '\n' + user_prompt)

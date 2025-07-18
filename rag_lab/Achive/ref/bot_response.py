from dotenv import load_dotenv
import os

load_dotenv(override=True)
api = os.getenv("API2")
model = "gpt-4o-mini"

from openai import OpenAI
client = OpenAI(api_key=api)

def bot_response(history):
    response = client.chat.completions.create(
        model=model,
        messages=history,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
    )
    return response
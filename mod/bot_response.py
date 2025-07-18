from dotenv import load_dotenv
import os
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv(override=True)
api = os.getenv("API2")
model = "gpt-4o-mini"


def bot_response(history):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    prompt = ChatPromptTemplate.from_template(
        "History: {history}\nQuestion: {input}"
    )
    chain = prompt | llm

    for chunk in chain.stream({
        "input": history[-1]["content"],  # 가장 최근 질문
        "history": history
    }):
        if hasattr(chunk, "content") and chunk.content:
            yield chunk.content
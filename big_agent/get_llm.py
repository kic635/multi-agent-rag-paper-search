import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from constants.SYSTEM_PROMPT import SYSTEM_PROMPT

# 加载环境变量
load_dotenv()
def get_llm():
    llm = ChatOpenAI(
        api_key=os.environ.get("DEEP_SEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        model="deepseek-reasoner",
        streaming=True,
        temperature=0.7,
    )
    return llm
llm = get_llm()
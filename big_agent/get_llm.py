import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from constants.SYSTEM_PROMPT import SYSTEM_PROMPT

# 加载环境变量
load_dotenv()
from langchain_deepseek import ChatDeepSeek
def get_llm():
    llm = ChatDeepSeek(
        api_key=os.environ.get("DEEP_SEEK_API_KEY"),
        model="deepseek-chat",
        streaming=True,
        temperature=0.7,
        model_kwargs={
            "parallel_tool_calls": False
        }
    )
    return llm
llm = get_llm()
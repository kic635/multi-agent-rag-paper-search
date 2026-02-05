import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from demo_agent import llm,SYSTEM_PROMPT
load_dotenv()
class AcademicRAGAgent:
    def __init__(self,tools):
        self.agent=create_agent(model=llm,system_prompt=SYSTEM_PROMPT,tools=tools)
    def ask(self,query:str):
        return self.agent.invoke({"input":query})

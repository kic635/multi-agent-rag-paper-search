from langchain_core.tools import Tool
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()

def get_tavily(query:str):
    response_data=[]
    client = TavilyClient(os.environ.get("TAVILY_API_KEY"))
    result = client.search(query=query)
    return result["results"]
tavily_tool=Tool(
    name="Tavily",
    description="A tool to search the internet using Tavily API",
    func=get_tavily
)









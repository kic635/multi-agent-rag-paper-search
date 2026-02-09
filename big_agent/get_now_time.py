import datetime
import datetime

from langchain_core.tools import Tool


def get_now_time(query: str):
    print("Getting current time...==========================")
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
now_tool=Tool(
    name="get_now_time",
    description="Get the current time in YYYY-MM-DD HH:MM:SS format",
    func=get_now_time
)
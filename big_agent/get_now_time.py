import datetime

from langchain_core.tools import Tool


def get_now_time():
    now = datetime.now()
    return now.strftime("%H:%M:%S")
now_tool=Tool(
    name="get_now_time",
    description="Get the current time in HH:MM:SS format",
    func=get_now_time
)
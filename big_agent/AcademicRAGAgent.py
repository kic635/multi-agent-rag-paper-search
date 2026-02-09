from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver

from demo_agent import llm
agent_mine = create_agent(
    model=llm,
    checkpointer=InMemorySaver()
)
if __name__ == '__main__':

   for chunk in agent_mine.stream(
       {"messages": [HumanMessage(content="What is the capital of France?")]},
       config={"configurable": {"thread_id": "2"}},
       stream_mode="messages"
   ):
          print(type(chunk))




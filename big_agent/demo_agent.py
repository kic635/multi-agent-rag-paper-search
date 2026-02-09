from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_classic.agents import AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import os
import psycopg
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.prompts import ChatPromptTemplate
system_prompt =ChatPromptTemplate([
    ("system", "你是一个{role}助手，使用{language}回答关于{topic}的问题。")
])

SYSTEM_PROMPT = (
    "你是一个集成多智能体协作能力且具备深厚 RAG (检索增强生成) 经验的高级学术助手。\n\n"
    "### 执行准则：\n"
    "1. **知识对齐 (Grounding)**：你的回答必须严格基于检索到的参考资料。若资料中未提及相关信息，"
    "2. **严谨性**：保持中立、客观的学术语气。论证需逻辑自洽，引用事实需精确。\n"
    "3. **工具边界**：仅在授权范围内调用工具。若任务超出工具能力或 RAG 检索范围，请说明局限性而非强行执行。\n"
    "4. **结构化输出**：使用清晰的标题、列表和术语，确保回答的高信息密度与逻辑层次。\n"
    "5. **意图识别**：根据用户意图进行回复，若基于知识库搜索不到，可基于你的知识回答内容，若知识储备不足，可以调用联网搜索的工具，优化用户的体验，一定要回答用户的问题"
)
load_dotenv()
llm=ChatOpenAI(
    api_key=os.environ.get("DEEP_SEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    streaming=True
)
DB_URI = "postgresql://postgres:123456@localhost:5432/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    agent_mine = create_agent(
        model=llm,
        checkpointer=checkpointer,
    )
    state= agent_mine.get_state({"configurable": {"thread_id": "1"}})
    msg=state.values['messages']
    conversation = []
    for message in msg:
        if isinstance(message, HumanMessage):
            conversation.append({"role": "user", "content": message.content})
        if isinstance(message, AIMessage):
            conversation.append({"role": "assistant", "content": message.content})
    print(conversation)
   # res=agent_mine.invoke({"messages":"谁发明了广义相对论"},{"configurable": {"thread_id": "1"}})
   #  conversation=[]
   #  history = agent_mine.get_state_history({"configurable": {"thread_id": "1"}})
   #  history = list(history)
   #  sum_history=(history[0].values["messages"])
   #  for message in sum_history:
   #      if isinstance(message, HumanMessage):
   #          conversation.append({"role": "user", "content": message.content})
   #      if isinstance(message, AIMessage):
   #          conversation.append({"role": "assistant", "content": message.content})
   #  print(conversation)
    # for checkpoint in history:
    #     print(f'我打印了{i}')
    #     i += 1
    #     messages = checkpoint.values["messages"]
    #     # 只提取 AIMessage 和 HumanMessage
    #     for msg in messages:
    #         if msg.__class__.__name__ in ["AIMessage", "HumanMessage"]:
    #             all_messages.append({
    #                 "type": msg.__class__.__name__,
    #                 "content": msg.content,
    #                 "id": msg.id
    #             })
    #
    # # 格式化输出
    # print("=== 历史对话记录 ===")
    # for msg in all_messages:
    #     print(f"\n[{msg['type']}]")
    #     print(f"内容: {msg['content'][:200]}...")  # 只显示前200字符
    #     print(f"ID: {msg['id']}")


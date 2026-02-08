from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select
from tenacity import sleep

from big_agent.get_llm import llm
from config.db_conf import get_db
from constants.PDB_URI import DB_URI
from crud.users import get_user_by_username, create_user,create_token,authenticate_user
from models.conversation import Conversation
from models.users import User
from schemas.users import UserRequest
from utils.auth import get_current_user
from fastapi.responses import StreamingResponse
from constants.SYSTEM_PROMPT import SYSTEM_PROMPT
router = APIRouter(prefix="/api/user", tags=["users"])




@router.post("/register")
async def register(user_data:UserRequest,db=Depends(get_db)):
    user=await get_user_by_username(user_data.username,db)
    if user:
        raise HTTPException(status_code=400,detail="User already exists")
    else:
       user=User(
            username=user_data.username,
            password=user_data.password )
       user=await create_user(user_data,db)
       token=await create_token(user.id,db)
    return{
        "code": 200,
        "message": "User created successfully",
        "data":{
            "token":token,
            "userInfo":{
                "id":user.id,
                "username":user.username,
                "bio":user.bio,
                "avatar":user.avatar,
            }
        }
    }
@router.post("/login")
async def login(user_data:UserRequest,db=Depends(get_db)):
    user=await authenticate_user(user_data,db)
    if not user:
        raise HTTPException(status_code=400,detail="Incorrect username or password")
    else:
       token=await create_token(user.id,db)
    return token
@router.get("/info")
async def get_user(db=Depends(get_db), user_id=Depends(get_current_user)):
    stmt=select(User).where(User.id == user_id)
    res=await db.execute(stmt)
    user=res.scalars().one_or_none()
    if not user:
        raise HTTPException(status_code=400,detail="User not found")
    return {
        "code": 200,
        "message": "success",
        "data":{
            "id":user.id,
            "username":user.username,
            "bio":user.bio,
            "avatar":user.avatar,
            "nike_name":user.nickname,
            "gender":user.gender,
        }
    }
@router.get("/chat")
async def chat(session_id:str,query:str,db=Depends(get_db), user_id=Depends(get_current_user)):
    #查这个session_id有没有存储在数据库中
    stmt=select(Conversation).where(Conversation.session_id == session_id)
    res=await db.execute(stmt)
    conversation=res.scalars().one_or_none()
    if conversation is None:
        conversation = Conversation(session_id=session_id, user_id=user_id)
        db.add(conversation)
        await db.commit()
    async def generate():
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
            agent_mine = create_agent(
                model=llm,
                checkpointer=checkpointer,
                system_prompt=SYSTEM_PROMPT
            )
            async for chunk in agent_mine.astream(
                {"messages": [HumanMessage(content=query)]},
                config={"configurable": {"thread_id": session_id}}
            ):
                if chunk and len(chunk) > 0:
                    yield chunk['model']['messages'][0].content
    
    return StreamingResponse(generate(), media_type="text/plain")
@router.get("/history")
async def get(session_id:str,db=Depends(get_db), user_id=Depends(get_current_user)):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        agent_mine = create_agent(
            model=llm,
            checkpointer=checkpointer,
            system_prompt=SYSTEM_PROMPT
        )
        configg={"configurable": {"thread_id": session_id}}
        state=await agent_mine.aget_state(configg)
        msg = state.values['messages']
        conversation = []
        for message in msg:
            if isinstance(message, HumanMessage):
                conversation.append({"role": "user", "content": message.content})
            if isinstance(message, AIMessage):
                conversation.append({"role": "assistant", "content": message.content})
    return {"code": 200, "message": "success", "data": conversation}
@router.get("/session_id_list")
async def session_id_list(user_id=Depends(get_current_user),db=Depends(get_db)):
    #根据user_id查询会话列表
    stmt=select(Conversation.session_id).where(Conversation.user_id == user_id)
    res=await db.execute(stmt)
    session_id_list = res.scalars().all()
    if not session_id_list:
        raise HTTPException(status_code=400,detail="User not found")
    return {"code": 200, "message": "success", "data": session_id_list}





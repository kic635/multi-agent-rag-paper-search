#根据用户名查询用户
import uuid
from datetime import datetime, timedelta

from fastapi import Depends
from pydantic import UUID4
from sqlalchemy import select

from config.db_conf import get_db
from models.users import User, UserToken
from schemas.users import UserRequest


async def get_user_by_username(username:str,db):
    #写完不管怎么样都执行一下
    query = select(User).where(User.username == username)
    res =await db.execute(query)
    return res.scalars().one_or_none()
async def create_user(user_data:UserRequest,db):
    user=User(**user_data.__dict__)
    db.add(user)
    await db.commit()
    #数据库更改了要refresh
    await db.refresh(user)
    return user
async def create_token(user_id, db=Depends(get_db)):
    #创建token->获取过期时间->如果有token 就刷新，如果没有就创建
    token=str(uuid.uuid4())
    expires_at=datetime.now()+timedelta(days=7)
    stmt=select(UserToken).where(UserToken.user_id == user_id, UserToken.expires_at > datetime.now())
    res=await db.execute(stmt)
    user_token=res.scalars().one_or_none()
    if user_token:
        user_token.token=token
        user_token.expires_at=expires_at
        await db.commit()
    else:
        user_token=UserToken(token=token,expires_at=expires_at,user_id=user_id)
        db.add(user_token)
        await db.commit()
    return token
async def authenticate_user(user_data,db):
    stmt=select(User).where(User.username == user_data.username and User.password == user_data.password)
    res=await db.execute(stmt)
    user=res.scalars().one_or_none()
    print(f'打印了{user}')
    if user:
        return user
    else:
        return False

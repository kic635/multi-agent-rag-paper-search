from datetime import datetime

from sqlalchemy import select

from models.users import User, UserToken
from fastapi import Header, Depends
from config.db_conf import get_db
async def get_current_user(authorization:str=Header(...,alias="Authorization"),db=Depends(get_db)):
    token=authorization
    #通过UserToken表查use_id
    stmt=select(UserToken).where(UserToken.token==token,UserToken.expires_at>datetime.now())
    res=await db.execute(stmt)
    user_token=res.scalars().one_or_none()
    return user_token.user_id
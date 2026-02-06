from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from config.db_conf import get_db
from crud.users import get_user_by_username, create_user,create_token,authenticate_user
from models.users import User
from schemas.users import UserRequest
from utils.auth import get_current_user
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


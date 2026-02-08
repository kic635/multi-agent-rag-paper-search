from fastapi import FastAPI
from router import Knowledge_Base_router
from router import users_router

app = FastAPI()


app.include_router(users_router.router)
app.include_router(Knowledge_Base_router.router)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from router import Knowledge_Base_router
from router import users_router
import os

app = FastAPI()

# 配置CORS - 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# 路由
app.include_router(users_router.router)
app.include_router(Knowledge_Base_router.router)

# 根路径返回前端页面
@app.get("/")
async def read_root():
    return FileResponse(os.path.join(frontend_path, "index.html"))
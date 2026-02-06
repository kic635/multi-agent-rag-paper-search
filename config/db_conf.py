# 1. 导入必要的模块
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,  # 注意：原代码中"async_sessionmaker"拼写错误
    AsyncSession,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase  # 用于定义模型基类


# 2. 数据库连接配置（根据你的实际环境修改）
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/big_rag?charset=utf8mb4"
# 说明：
# - root: 数据库用户名
# - 123456: 数据库密码
# - localhost: 数据库地址（本地）
# - 3306: MySQL默认端口
# - news_app: 数据库名
# - charset=utf8mb4: 字符集（支持emoji）


# 3. 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,          # 开发环境：输出SQL日志（方便调试）；生产环境建议改为False
    pool_size=10,       # 连接池默认保持的连接数
    max_overflow=20     # 连接池允许临时创建的额外连接数
)


# 4. 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,       # 绑定异步引擎
    class_=AsyncSession,     # 指定会话类为AsyncSession
    expire_on_commit=False   # 提交后不自动过期对象（避免重复查询）
)




# 6. 依赖项：获取数据库会话（供FastAPI接口使用）
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 提供会话给接口
            await session.commit()  # 接口逻辑执行成功后，提交事务
        except Exception as e:
            await session.rollback()  # 发生异常时回滚事务
            raise e  # 抛出异常，让FastAPI捕获并返回错误
        finally:
            await session.close()  # 最终关闭会话
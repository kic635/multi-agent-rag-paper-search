from datetime import datetime
from typing import Optional

from sqlalchemy import Index, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass
class Conversation(Base):
    __tablename__ = "conversation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="对话id")
    session_id: Mapped[int] = mapped_column(Integer,unique=True,comment="会话id")
    user_id:Mapped[int]=mapped_column(Integer, nullable=False, comment="用户id")
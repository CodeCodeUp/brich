from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# 依赖注入：获取 DB 会话
from fastapi import Depends
import os

# 从环境变量读取 MySQL 连接
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost/dbname?charset=utf8mb4")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
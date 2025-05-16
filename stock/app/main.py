from fastapi import FastAPI
from .routers import daily_change, stock_chart
from .database import Base, engine

# 创建表（生产环境推荐 Alembic 管理迁移）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Change & Chart API")
app.include_router(daily_change.router)
app.include_router(stock_chart.router)
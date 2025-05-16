from sqlalchemy import Column, Integer, Date, String, Enum, DECIMAL, DateTime, ForeignKey, UniqueConstraint
from .database import Base
from enum import Enum as PyEnum

class ChangeType(PyEnum):
    INCREASE = "增持"
    DECREASE = "减持"

class DailyStockChange(Base):
    __tablename__ = "daily_stock_change"
    record_id       = Column(Integer, primary_key=True, autoincrement=True)
    trade_date      = Column(Date, nullable=False)
    stock_code      = Column(String(10), nullable=False)
    stock_name      = Column(String(50), nullable=False)
    change_type     = Column(Enum(ChangeType), nullable=False)
    changer_name    = Column(String(50), nullable=False)
    changer_position= Column(String(100))
    change_shares   = Column(DECIMAL(18,2), nullable=False)
    price           = Column(DECIMAL(10,2), nullable=False)
    total_price     = Column(DECIMAL(18,2), nullable=False)
    after_shares    = Column(DECIMAL(18,2), nullable=False)
    change_ratio    = Column(DECIMAL(10,6))
    change_reason   = Column(String(50))
    company_id      = Column(Integer)
    is_public       = Column(Integer, default=1)
    create_time     = Column(DateTime)
    update_time     = Column(DateTime)
    __table_args__ = (
        UniqueConstraint('trade_date','stock_code','changer_name','change_shares','after_shares', name='daily_stock_change_trade_date_IDX'),
    )

class StockBase(Base):
    __tablename__ = "stock_base"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    stock_code   = Column(String(10), unique=True)
    stock_name   = Column(String(10))
    begin_time   = Column(DateTime)

class StockPriceTracking(Base):
    __tablename__ = "stock_price_tracking"
    track_id     = Column(Integer, primary_key=True, autoincrement=True)
    stock_code   = Column(String(10), nullable=False)
    track_time   = Column(DateTime, nullable=False)
    current_price= Column(DECIMAL(10,2), nullable=False)
    open_price   = Column(DECIMAL(10,2), nullable=False)
    high_price   = Column(DECIMAL(10,2), nullable=False)
    low_price    = Column(DECIMAL(10,2), nullable=False)
    volume       = Column(Integer, nullable=False)
    amount       = Column(DECIMAL(18,2), nullable=False)
    change_rate  = Column(DECIMAL(5,2), nullable=False)
    error_msg    = Column(String(255))
    create_time  = Column(DateTime)
    __table_args__ = (
        UniqueConstraint('stock_code','track_time', name='unique_track_time'),
    )
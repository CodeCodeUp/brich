from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from app.models import ChangeType

class DailyChangeItem(BaseModel):
    trade_date: date
    stock_code: str
    stock_name: str
    total_increase: Decimal
    total_decrease: Decimal

class StockMark(BaseModel):
    trade_date: date
    change_type: ChangeType
    shares: Decimal

class PricePoint(BaseModel):
    track_time: datetime
    current_price: Decimal

class ChartData(BaseModel):
    price_data: List[PricePoint]
    marks: List[StockMark]
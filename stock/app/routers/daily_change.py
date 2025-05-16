from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/daily-changes", tags=["DailyChange"])

@router.get("/", response_model=List[schemas.DailyChangeItem])
async def list_daily_changes(
    start: date = Query(...),
    end: date = Query(...),
    db: Session = Depends(get_db)
):
    q = (
        db.query(
            models.DailyStockChange.trade_date,
            models.DailyStockChange.stock_code,
            models.DailyStockChange.stock_name,
            func.sum(case([(models.DailyStockChange.change_type == models.ChangeType.INCREASE, models.DailyStockChange.change_shares)], else_=0)).label("total_increase"),
            func.sum(case([(models.DailyStockChange.change_type == models.ChangeType.DECREASE, models.DailyStockChange.change_shares)], else_=0)).label("total_decrease")
        )
        .filter(models.DailyStockChange.is_public == 1)
        .filter(models.DailyStockChange.trade_date.between(start, end))
        .group_by(models.DailyStockChange.trade_date, models.DailyStockChange.stock_code, models.DailyStockChange.stock_name)
    )
    return q.all()
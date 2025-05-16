from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from datetime import date

router = APIRouter(prefix="/api/stock", tags=["StockChart"])

@router.get("/{code}/chart", response_model=schemas.ChartData)
async def get_stock_chart(
    code: str,
    start: date,
    end: date,
    db: Session = Depends(get_db)
):
    # 股价序列
    price_rows = (
        db.query(models.StockPriceTracking.track_time, models.StockPriceTracking.current_price)
          .filter(models.StockPriceTracking.stock_code == code)
          .filter(models.StockPriceTracking.track_time.between(start, end))
          .order_by(models.StockPriceTracking.track_time)
          .all()
    )
    if not price_rows:
        raise HTTPException(404, "No price data found")

    # 增减持汇总
    mark_rows = (
        db.query(
            models.DailyStockChange.trade_date,
            models.DailyStockChange.change_type,
            func.sum(models.DailyStockChange.change_shares).label("shares")
        )
        .filter(models.DailyStockChange.stock_code == code)
        .filter(models.DailyStockChange.is_public == 1)
        .filter(models.DailyStockChange.trade_date.between(start, end))
        .group_by(models.DailyStockChange.trade_date, models.DailyStockChange.change_type)
        .all()
    )

    price_data = [schemas.PricePoint(track_time=r.track_time, current_price=r.current_price) for r in price_rows]
    marks = [schemas.StockMark(trade_date=r.trade_date, change_type=r.change_type, shares=r.shares) for r in mark_rows]
    return schemas.ChartData(price_data=price_data, marks=marks)
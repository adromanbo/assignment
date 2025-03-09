from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from stocks.core.database import get_db
from stocks.schemas.daily_ticker import DailyTickerCreate, DailyTickerResponse

router = APIRouter()

@router.post("/", response_model=DailyTickerResponse)
def add_daily_ticker(data: DailyTickerCreate, db: Session = Depends(get_db)):
    return create_daily_ticker(db, data)

@router.get("/", response_model=list[DailyTickerResponse])
def list_daily_tickers(db: Session = Depends(get_db)):
    return get_all_daily_tickers(db)

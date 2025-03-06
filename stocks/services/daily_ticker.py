from sqlalchemy.orm import Session
from stocks.models.daily_ticker import DailyTicker
from stocks.schemas.daily_ticker import DailyTickerCreate

def create_daily_ticker(db: Session, data: DailyTickerCreate):
    db_ticker = DailyTicker(**data.dict())
    db.add(db_ticker)
    db.commit()
    db.refresh(db_ticker)
    return db_ticker

def get_all_daily_tickers(db: Session):
    return db.query(DailyTicker).all()
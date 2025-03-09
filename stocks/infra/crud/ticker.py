from sqlalchemy.orm import Session
from stocks.models.daily_ticker import DailyTicker


def create_ticker(db: Session, date: str, ticker: str, price: int) -> DailyTicker:
    new_ticker = DailyTicker(date=date, ticker=ticker, price=price)
    db.add(new_ticker)
    db.commit()
    db.refresh(new_ticker)
    return new_ticker

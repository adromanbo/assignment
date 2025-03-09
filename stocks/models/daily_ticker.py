from sqlalchemy import Column, String, Numeric, Date
from stocks.models.base import Base

class DailyTicker(Base):
    __tablename__ = "daily_ticker"

    date = Column(Date, primary_key=True, nullable=False, index=True)
    ticker = Column(String(10), primary_key=True, nullable=False, index=True)
    price = Column(Numeric(13, 4), nullable=False)

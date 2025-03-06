from sqlalchemy import Column, Integer, String, Numeric, Date

from stocks.core.database import Base

"""
date	Date	2020-01-01
ticker	Varchar(10)	SPY
price	Numeric(13,4)	298.2208
"""

class DailyTicker(Base):
    __tablename__ = "daily_ticker"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, primary_key=True, index=True, nullable=False)
    ticker = Column(String(10), index=True, nullable=False)
    price = Column(Numeric(13, 4), nullable=False)

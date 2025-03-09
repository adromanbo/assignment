from pydantic import BaseModel
from datetime import date


class DailyTickerBase(BaseModel):
    date: date
    ticker: str
    price: float


class DailyTickerCreate(DailyTickerBase):
    pass


class DailyTickerResponse(DailyTickerBase):
    class Config:
        from_attributes = True

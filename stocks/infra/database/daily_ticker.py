from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from stocks.models import DailyTicker


class DailyTickerRepo:
    @staticmethod
    def fetch_ticker_data(session: Session, start_date: datetime) -> pd.DataFrame:
        """
        DB에서 주어진 날짜 이후의 가격 데이터를 불러온다.
        주말(토, 일)은 제외한다.
        """
        query = select(DailyTicker).where(DailyTicker.date >= start_date)
        df = pd.read_sql(query, session.bind)
        df["date"] = pd.to_datetime(df["date"])
        return df


daily_ticker_repo = DailyTickerRepo()

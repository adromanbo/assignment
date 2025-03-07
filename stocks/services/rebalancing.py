import math
from datetime import datetime, timedelta
from typing import Dict

import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from stocks.core.database import SessionLocal
from stocks.models.daily_ticker import DailyTicker
from utils.constant import AccountStatus, PurchaseListObject, TickerInfo


def fetch_stock_data(session: Session, start_date: datetime):
    """
    DB에서 주어진 날짜 이후의 가격 데이터를 불러온다.
    주말(토, 일)은 제외한다.
    """
    query = select(DailyTicker).where(DailyTicker.date >= start_date)
    df = pd.read_sql(query, session.bind)
    df["date"] = pd.to_datetime(df["date"])
    return df


def calculate_rebalancing_weights(
    ticker_info: dict[str, TickerInfo],
    df: pd.DataFrame,
    start_date: pd.Timestamp,
    period_months: int,
    top_n: int = 2,
):
    df_tip = df.query("ticker == 'TIP'")

    # 날짜 필터링 (최근 3개월)
    tip_cutoff_date = start_date - pd.DateOffset(months=3)
    tip_df_filtered = df_tip[df_tip["date"].between(tip_cutoff_date, start_date)]

    tip_profit = 1 - tip_df_filtered.iloc[0].price / tip_df_filtered.iloc[-1].price

    cutoff_date = start_date - pd.DateOffset(months=period_months)
    df_filtered = df[df["date"].between(cutoff_date, start_date)]

    for ticker, ticker_data in df_filtered.groupby("ticker"):
        ticker_info[ticker].momentum = calculate_momentum(ticker_data)
        ticker_info[ticker].profit_rate = (
            round(ticker_data.iloc[-1].price / ticker_info[ticker].current_price, 5)
            if ticker_info[ticker].current_price != 0
            else 0
        )
        ticker_info[ticker].current_price = ticker_data.iloc[-1].price

    for ticker, info in ticker_info.items():
        info.weight = 0

    buy_bil = True if tip_profit < 0 else False
    if buy_bil:
        for ticker, info in ticker_info.items():
            if ticker == "BIL":
                info.weight = 1
        return

    # BIL과 TIP을 제외한 종목만 필터링
    filtered_tickers = {k: v for k, v in ticker_info.items() if k not in {"BIL", "TIP"}}

    # 모멘텀 기준으로 정렬
    sorted_tickers = sorted(
        filtered_tickers.items(), key=lambda x: x[1].momentum, reverse=True
    )

    # top_n개 선택 후 weight 설정
    for i, (ticker, info) in enumerate(sorted_tickers):
        if i < top_n:
            info.weight = 0.5


def calculate_statistics(nav_history: list):
    """
    NAV 변동을 기반으로 누적 수익률, 연평균 수익률, 변동성을 계산한다.
    """
    df = pd.DataFrame({"NAV": nav_history})
    df["returns"] = df["NAV"].pct_change()
    cumulative_return = (df["NAV"].iloc[-1] / df["NAV"].iloc[0]) - 1
    annualized_return = (1 + cumulative_return) ** (1 / (len(df) / 12)) - 1
    volatility = df["returns"].std()
    return {
        "cumulative_return": cumulative_return,
        "annualized_return": annualized_return,
        "volatility": volatility,
    }


def get_next_trading_date(df, current_date, trading_day, trading_month_period):
    """
    다음 리밸런싱 날짜를 찾는 함수.
    - 기본적으로 다음 달 `trading_day`을 목표로 함
    - 만약 존재하지 않는 날짜라면, 가장 가까운 이전 날짜를 선택
    """
    next_month = current_date + relativedelta(months=trading_month_period)
    target_date = datetime(next_month.year, next_month.month, trading_day)
    # 해당 날짜가 존재하는지 확인
    available_dates = df[target_date >= df["date"]]["date"]
    return available_dates.max()


class RebalancingService:
    def __init__(self):
        self.account_status = AccountStatus()
        self.ticker_info: dict[str, TickerInfo] = {}
        self.total_nav = 0

    def execute_trades(
        self,
        trading_fee: float,
    ):
        """
        리밸런싱 후 NAV를 계산한다.
        """

        for stock_code, info in self.ticker_info.items():
            info.before_nav = round(info.after_nav * info.profit_rate, 2)
            self.total_nav += info.before_nav - info.target_nav

        print(self.total_nav , "total_nav")
        for stock_code, info in self.ticker_info.items():
            # TODO 구매 후 남은 잔액은 어떻게 할까?
            purchase_amount = round(self.total_nav * info.weight, 2)
            print(info.before_nav)
            purchase_amount = round(purchase_amount - info.before_nav, 2)

            info.target_nav = purchase_amount + info.before_nav
            info.after_nav = round(purchase_amount + info.before_nav, 2)
            info.fee = round(abs(purchase_amount) * trading_fee, 2)
            print(
                purchase_amount,
                stock_code,
                "purchase_amount",
                info.profit_rate,
                info.after_nav,
                info.target_nav,
            )
        total_fee = sum(
            [info.fee for info in self.ticker_info.values()]
        )

        for stock_code, info in self.ticker_info.items():
            info.after_nav = round(info.after_nav - round(total_fee * info.weight, 2), 2)
            print(info.after_nav, "after_nav")

        self.account_status.current_nav = self.total_nav - total_fee

    def run_rebalancing(
        self,
        session: Session,
        start_year: int,
        start_month: int,
        initial_nav: float,
        trading_day: int,
        trading_fee: float,
        rebalance_month_period: int,
        trading_month_period: int = 1,
    ) -> dict:
        """
        리밸런싱 프로세스를 실행하는 메인 함수
        """
        start_date = datetime(start_year, start_month, trading_day)
        stock_data = fetch_stock_data(session, start_date - timedelta(days=200))
        nav_history = [initial_nav]

        self.account_status.initial_nav = initial_nav
        self.total_nav = initial_nav
        self.account_status.current_nav = initial_nav

        self.ticker_info = {
            ticker: TickerInfo() for ticker in stock_data["ticker"].unique()
        }
        cnt = 0
        while True:
            print("\nstart_date", start_date)
            calculate_rebalancing_weights(
                self.ticker_info, stock_data, start_date, rebalance_month_period
            )
            print(
                self.ticker_info["SPY"].weight,
                self.ticker_info["QQQ"].weight,
                self.ticker_info["GLD"].weight,
                self.ticker_info["BIL"].weight,
                "weight",
            )

            self.execute_trades(trading_fee)

            nav_history.append(self.account_status.current_nav)
            before_date = start_date
            start_date = get_next_trading_date(
                stock_data, start_date, trading_day, trading_month_period
            )
            if start_date == before_date:
                break

        stats = calculate_statistics(nav_history)
        print({"final_nav": self.account_status.current_nav, "statistics": stats})
        return {"final_nav": self.account_status.current_nav, "statistics": stats}


def calculate_momentum(stock_prices: pd.DataFrame):
    """모멘텀 계산 (절대/상대 모멘텀 적용 가능)"""
    initial_price = stock_prices.iloc[0].price
    latest_price = stock_prices.iloc[-1].price
    return (latest_price - initial_price) / initial_price


def calculate_profit_rate(stock_prices: pd.DataFrame):
    initial_price = stock_prices.iloc[0].price
    latest_price = stock_prices.iloc[-1].price
    print(stock_prices.iloc[-1])
    print(latest_price / initial_price, initial_price, latest_price, "profit_rate")
    return latest_price / initial_price


rebalancing_service = RebalancingService()

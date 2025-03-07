from datetime import datetime, timedelta
from decimal import Decimal
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
    ticker_info: dict[str, TickerInfo], df: pd.DataFrame, start_date: pd.Timestamp, period_months: int, top_n: int = 2
):
    cutoff_date = start_date - pd.DateOffset(months=period_months)
    df_filtered = df[df["date"].between(cutoff_date, start_date)]


    for ticker, ticker_data in df_filtered.groupby("ticker"):
        ticker_info[ticker].momentum = calculate_momentum(ticker_data)
        ticker_info[ticker].profit_rate = round(ticker_data.iloc[-1].price / ticker_info[ticker].current_price, 9) if ticker_info[ticker].current_price != 0 else 0
        ticker_info[ticker].current_price = ticker_data.iloc[-1].price
        print(ticker_info[ticker].momentum, ticker_info[ticker].current_price, ticker_info[ticker].profit_rate, ticker)

    buy_bil = True if ticker_info["TIP"].momentum < 0 else False

    if buy_bil:
        ticker_info["BIL"].weight = 1
        return

    # top_n개의 ticker를 선택해서 weight를 0.5로 설정
    sorted_tickers = sorted(ticker_info.items(), key=lambda x: x[1].momentum, reverse=True)
    for i, (ticker, info) in enumerate(sorted_tickers[:top_n]):
        info.weight = 0.5

from decimal import Decimal, ROUND_DOWN

def execute_trades(
    ticker_info: Dict[str, TickerInfo],
    account_status: AccountStatus,
    trading_fee: float,
):
    """
    리밸런싱 후 NAV를 계산한다.
    """
    rounding = Decimal("0.01")  # 소숫점 2자리까지 제한

    total_nav = account_status.current_nav
    for stock_code, info in ticker_info.items():
        # TODO 구매 후 남은 잔액은 어떻게 할까?
        print(info.after_nav, "info.after_nav")
        info.before_nav = info.after_nav * Decimal(1 + info.profit_rate)
        print(info.before_nav, "info.before_nav")
        purchase_amount = (total_nav * Decimal(info.weight)).quantize(rounding, rounding=ROUND_DOWN)
        purchase_amount = (purchase_amount - info.before_nav).quantize(rounding, rounding=ROUND_DOWN)
        print(purchase_amount, stock_code, "purchase_amount", Decimal(1 - trading_fee))

        info.target_nav = purchase_amount
        info.after_nav = (purchase_amount * Decimal(1 - trading_fee)).quantize(rounding, rounding=ROUND_DOWN)
        info.fee = purchase_amount * Decimal(trading_fee).quantize(rounding, rounding=ROUND_DOWN)
        print(purchase_amount, stock_code, "purchase_amount")

    return account_status


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

    def run_rebalancing(
        self,
        session: Session,
        start_year: int,
        start_month: int,
        initial_nav: float,
        trading_day: int,
        trading_fee: Decimal,
        rebalance_month_period: int,
        trading_month_period: int = 1,
    ) -> dict:
        """
        리밸런싱 프로세스를 실행하는 메인 함수
        """
        start_date = datetime(start_year, start_month, trading_day)
        stock_data = fetch_stock_data(session, start_date - timedelta(days=200))
        nav_history = [initial_nav]

        self.account_status.initial_nav = Decimal(initial_nav)
        self.account_status.current_nav = Decimal(initial_nav)
        self.ticker_info = {
            ticker: TickerInfo()
            for ticker in stock_data["ticker"].unique()
        }
        cnt = 0
        while True:
            calculate_rebalancing_weights(
                self.ticker_info, stock_data, start_date, rebalance_month_period
            )
            print(self.ticker_info["SPY"].weight, self.ticker_info["QQQ"].weight, self.ticker_info["GLD"].weight, self.ticker_info["BIL"].weight, "weight")

            execute_trades(
                self.ticker_info, self.account_status, trading_fee
            )
            print(
                self.account_status.current_nav,
            )
            nav_history.append(self.account_status.current_nav)
            before_date = start_date
            start_date = get_next_trading_date(
                stock_data, start_date, trading_day, trading_month_period
            )
            cnt += 1
            if cnt > 2:
                break
            if start_date == before_date:
                break

        stats = calculate_statistics(nav_history)
        print(nav_history)
        print({"final_nav": account_status.current_nav, "statistics": stats})
        return {"final_nav": account_status.current_nav, "statistics": stats}


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
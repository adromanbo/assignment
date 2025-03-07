from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import daily_ticker  # DB 모델


def fetch_price_data(session: Session, start_date: datetime):
    """
    DB에서 주어진 날짜 이후의 가격 데이터를 불러온다.
    주말(토, 일)은 제외한다.
    """
    query = select(daily_ticker).where(daily_ticker.date >= start_date)
    df = pd.read_sql(query, session.bind)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.weekday < 5]  # 주말 제외
    return df


def calculate_rebalancing_weights(df: pd.DataFrame, period_months: int):
    """
    지정된 개월 수(period_months) 동안의 평균 가격을 기준으로 리밸런싱 비중을 계산한다.
    """
    cutoff_date = df['date'].max() - pd.DateOffset(months=period_months)
    df_filtered = df[df['date'] >= cutoff_date]
    avg_prices = df_filtered.groupby('ticker')['price'].mean()
    weights = avg_prices / avg_prices.sum()
    return weights.to_dict()


def execute_trades(nav: float, weights: dict, trading_fee: float):
    """
    리밸런싱 후 NAV를 계산한다.
    """
    allocated_funds = {ticker: nav * weight for ticker, weight in weights.items()}
    total_fee = sum(allocated_funds.values()) * trading_fee
    return nav - total_fee, allocated_funds


def calculate_statistics(nav_history: list):
    """
    NAV 변동을 기반으로 누적 수익률, 연평균 수익률, 변동성을 계산한다.
    """
    df = pd.DataFrame({'NAV': nav_history})
    df['returns'] = df['NAV'].pct_change()
    cumulative_return = (df['NAV'].iloc[-1] / df['NAV'].iloc[0]) - 1
    annualized_return = (1 + cumulative_return) ** (1 / (len(df) / 12)) - 1
    volatility = df['returns'].std()
    return {
        'cumulative_return': cumulative_return,
        'annualized_return': annualized_return,
        'volatility': volatility
    }


def run_rebalancing(session: Session, start_year: int, start_month: int, initial_nav: float,
                    trading_day: int, trading_fee: float, rebalance_period: int):
    """
    리밸런싱 프로세스를 실행하는 메인 함수
    """
    start_date = datetime(start_year, start_month, trading_day)
    df = fetch_price_data(session, start_date)
    nav = initial_nav
    nav_history = [nav]

    while start_date < df['date'].max():
        weights = calculate_rebalancing_weights(df[df['date'] <= start_date], rebalance_period)
        nav, _ = execute_trades(nav, weights, trading_fee)
        nav_history.append(nav)
        start_date += timedelta(days=30)  # 매월 진행

    stats = calculate_statistics(nav_history)
    return {
        'final_nav': nav,
        'statistics': stats
    }

import pandas as pd


def calculate_momentum(stock_prices: pd.DataFrame):
    """모멘텀 계산 (절대/상대 모멘텀 적용 가능)"""
    initial_price = stock_prices.iloc[0].price
    latest_price = stock_prices.iloc[-1].price
    return (latest_price - initial_price) / initial_price

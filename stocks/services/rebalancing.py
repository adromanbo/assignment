import math
from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from stocks.infra.database.daily_ticker import daily_ticker_repo
from utils.calculator import calculate_momentum
from utils.constant import AccountStatus, TickerInfo


class RebalancingService:
    def __init__(self):
        self.account_status = AccountStatus()
        self.ticker_info: dict[str, TickerInfo] = {}
        self.total_nav = 0

    def calculate_statistics(
        self, nav_history, trade_day, yearly_trade_day: int = 12
    ) -> Dict:
        """
        투자 성과 지표를 계산하는 함수

        Parameters:
            nav_history (list): 순자산 가치(NAV) 리스트
            trade_day (int): 거래일 수
            yearly_trade_day (int): 1년 거래일 수

        Returns:
            dict: 전체 기간 수익률, 연환산수익율, 연 변동성, 샤프지수, 최대 손실폭
        """
        nav = np.array(nav_history)

        # 전체 기간 수익률
        total_return = (nav[-1] / nav[0] - 1) * 100

        # 연환산 수익률 (CAGR)
        num_years = trade_day / 365
        cagr = ((nav[-1] / nav[0]) ** (1 / num_years) - 1) * 100

        # 일간 수익률
        daily_returns = np.diff(nav) / nav[:-1]

        # 연변동성 (Annualized Volatility)
        annualized_volatility = np.std(daily_returns) * np.sqrt(yearly_trade_day) * 100

        # 샤프 지수 (Sharpe Ratio) - 무위험 수익률 0으로 가정
        sharpe_ratio = (
            (cagr - 0) / annualized_volatility if annualized_volatility > 0 else np.nan
        )

        # 최대 손실폭 (Max Drawdown)
        running_max = np.maximum.accumulate(nav)
        drawdowns = (nav - running_max) / running_max
        max_drawdown = np.min(drawdowns) * 100

        return {
            "total_return": total_return,
            "cagr": cagr,
            "vol": annualized_volatility,
            "sharpe": sharpe_ratio,
            "mdd": max_drawdown,
        }

    def get_next_trading_date(
        self, df, current_date, trading_day, trading_month_period
    ):
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

    def calculate_rebalancing_weights(
        self,
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
            self.ticker_info[ticker].momentum = calculate_momentum(ticker_data)
            self.ticker_info[ticker].profit_rate = (
                round(
                    ticker_data.iloc[-1].price / self.ticker_info[ticker].current_price,
                    5,
                )
                if self.ticker_info[ticker].current_price != 0
                else 0
            )
            self.ticker_info[ticker].current_price = ticker_data.iloc[-1].price

        for ticker, info in self.ticker_info.items():
            info.weight = 0

        buy_bil = True if tip_profit < 0 else False
        if buy_bil:
            for ticker, info in self.ticker_info.items():
                if ticker == "BIL":
                    info.weight = 1
            return

        # BIL과 TIP을 제외한 종목만 필터링
        filtered_tickers = {
            k: v for k, v in self.ticker_info.items() if k not in {"BIL", "TIP"}
        }

        sorted_tickers = sorted(
            filtered_tickers.items(), key=lambda x: x[1].momentum, reverse=True
        )

        for i, (ticker, info) in enumerate(sorted_tickers):
            if i < top_n:
                info.weight = 0.5

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

        for stock_code, info in self.ticker_info.items():
            # TODO 구매 후 남은 잔액은 어떻게 할까?
            purchase_amount = round(self.total_nav * info.weight, 2)
            purchase_amount = round(purchase_amount - info.before_nav, 2)

            info.target_nav = purchase_amount + info.before_nav
            info.after_nav = round(purchase_amount + info.before_nav, 2)
            info.fee = round(abs(purchase_amount) * trading_fee, 2)
        total_fee = sum([info.fee for info in self.ticker_info.values()])

        for stock_code, info in self.ticker_info.items():
            info.after_nav = round(
                info.after_nav - round(total_fee * info.weight, 2), 2
            )

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
    ) -> (list, dict, list):
        """
        리밸런싱 프로세스를 실행하는 메인 함수

        Parameters:
            session (Session): DB 세션
            start_year (int): 시작 연도
            start_month (int): 시작 월
            initial_nav (float): 초기 자산가치
            trading_day (int): 거래일
            trading_fee (float): 거래 수수료
            rebalance_month_period (int): 리밸런싱 주기 (월)
            trading_month_period (int): 거래 주기 (월)

        Returns:
            최종 리밸런싱 비중 rebalance_weight   ||
            투자 성과 지표 stats
        """
        start_date = datetime(start_year, start_month, trading_day)
        stock_data = daily_ticker_repo.fetch_ticker_data(
            session, start_date - timedelta(days=200)
        )
        nav_history = [initial_nav]
        rebalance_weight_list = []

        self.account_status.initial_nav = initial_nav
        self.total_nav = initial_nav
        self.account_status.current_nav = initial_nav

        self.ticker_info = {
            ticker: TickerInfo() for ticker in stock_data["ticker"].unique()
        }
        while True:
            self.calculate_rebalancing_weights(
                stock_data, start_date, rebalance_month_period
            )

            self.execute_trades(trading_fee)

            nav_history.append(self.account_status.current_nav)
            before_date = start_date
            start_date = self.get_next_trading_date(
                stock_data, start_date, trading_day, trading_month_period
            )
            rebalance_weight_list.append(
                [(ticker, info.weight) for ticker, info in self.ticker_info.items()]
            )
            if start_date == before_date:
                break

        stats = self.calculate_statistics(
            nav_history,
            (start_date - datetime(start_year, start_month, trading_day)).days,
        )
        return rebalance_weight_list, stats, nav_history


rebalancing_service = RebalancingService()

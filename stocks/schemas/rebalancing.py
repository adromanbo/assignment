from pydantic import BaseModel
from datetime import date


class RebalanceInput(BaseModel):
    start_year: int
    start_month: int
    initial_nav: float
    trading_day: int
    trading_fee: float
    rebalance_month_period: int


class RebalanceProcessOutput(BaseModel):
    data_id: int
    output: dict
    last_rebalance_weight: list


class DeleteRebalanceDataOutput(BaseModel):
    data_id: int


class GetRebalanceAllDataOutput(BaseModel):
    data_list: list


class GetRebalanceDataOutput(BaseModel):
    input: dict
    output: dict
    last_rebalance_weight: list

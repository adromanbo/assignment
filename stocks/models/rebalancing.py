from sqlalchemy import Column, Integer, JSON
from stocks.models.base import Base


class RebalancingData(Base):
    __tablename__ = "rebalancing_data"

    data_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    rebalance_weight_list = Column(JSON, nullable=False)
    nav_history = Column(JSON, nullable=False)


def serialize_rebalancing_data(value):
    if isinstance(value, list):
        return [serialize_rebalancing_data(value) for value in value]
    else:
        return {
            "data_id": value.data_id,
            "input_data": value.input_data,
            "output_data": value.output_data,
            "rebalance_weight_list": value.rebalance_weight_list,
            "nav_history": value.nav_history,
        }

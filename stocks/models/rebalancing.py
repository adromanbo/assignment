from sqlalchemy import Column, String, Numeric, Date, Integer, JSON
from stocks.models.base import Base


class RebalancingData(Base):
    __tablename__ = "rebalance_data"

    data_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    input_data = Column(JSON, nullable=False)
    rebalance_weights = Column(JSON, nullable=False)
    nav_totals = Column(JSON, nullable=False)

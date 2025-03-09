from sqlalchemy.orm import Session
from stocks.models import RebalancingData


def create_rebalance_entry(
    db: Session, input_data: dict, last_rebalance_weight: list, nav_totals: list
) -> RebalancingData:
    new_entry = RebalancingData(
        input_data=input_data,
        rebalance_weights=last_rebalance_weight,
        nav_totals=nav_totals,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def get_rebalance_list(db: Session) -> list:
    return db.query(RebalancingData).all()


def get_rebalance_entry(db: Session, data_id: int) -> RebalancingData:
    return db.query(RebalancingData).filter(RebalancingData.data_id == data_id).first()

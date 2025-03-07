from sqlalchemy.orm import Session
from stocks.models import RebalanceData

def create_rebalance_entry(db: Session, input_data: dict, last_rebalance_weight: list, nav_totals: list):
    new_entry = RebalanceData(input_data=input_data, rebalance_weights=last_rebalance_weight, nav_totals=nav_totals)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

def get_rebalance_list(db: Session):
    return db.query(RebalanceData).all()

def get_rebalance_entry(db: Session, data_id: int):
    return db.query(RebalanceData).filter(RebalanceData.data_id == data_id).first()

def delete_rebalance_entry(db: Session, data_id: int):
    entry = db.query(RebalanceData).filter(RebalanceData.data_id == data_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return entry
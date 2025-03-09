from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from stocks.models.rebalancing import RebalancingData


class RebalancingRepo:
    @staticmethod
    def fetch_by_data_id(db: Session, data_id: int):
        return (
            db.query(RebalancingData).filter(RebalancingData.data_id == data_id).first()
        )

    @staticmethod
    def delete_by_data_id(db: Session, data_id: int):
        entry = (
            db.query(RebalancingData).filter(RebalancingData.data_id == data_id).first()
        )
        if entry:
            db.delete(entry)
            db.commit()
        return entry

    @staticmethod
    def fetch_all(db: Session, limit: int = 2000):
        return db.query(RebalancingData).all()[:limit]


rebalancing_repo = RebalancingRepo()

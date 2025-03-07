from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from stocks.core.database import SessionLocal, engine
from stocks.infra.crud import create_rebalance_entry, get_rebalance_list, get_rebalance_entry, delete_rebalance_entry
from stocks.models import Base

Base.metadata.create_all(bind=engine)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/rebalance/")
def create_entry(input_data: dict, db: Session = Depends(get_db)):
    # 가상의 계산 로직 적용
    last_rebalance_weight = [("SPY", 0.5), ("QQQ", 0.5), ("BIL", 0)]
    nav_totals = [100, 110, 120]

    entry = create_rebalance_entry(db, input_data, last_rebalance_weight, nav_totals)
    return {
        "data_id": entry.data_id,
        "output": {"total_return": 0.66, "cagr": 0.1043, "vol": 0.121, "sharpe": 0.86, "mdd": -0.1947},
        "last_rebalance_weight": last_rebalance_weight
    }


@router.get("/rebalance/")
def list_entries(db: Session = Depends(get_db)):
    entries = get_rebalance_list(db)
    return [{"data_id": entry.data_id, "last_rebalance_weight": entry.rebalance_weights} for entry in entries]


@router.get("/rebalance/{data_id}")
def get_entry(data_id: int, db: Session = Depends(get_db)):
    entry = get_rebalance_entry(db, data_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Data not found")
    return {
        "input": entry.input_data,
        "output": {"data_id": entry.data_id, "total_return": 0.66, "cagr": 0.1043, "vol": 0.121, "sharpe": 0.86,
                   "mdd": -0.1947},
        "last_rebalance_weight": entry.rebalance_weights
    }


@router.delete("/rebalance/{data_id}")
def delete_entry(data_id: int, db: Session = Depends(get_db)):
    entry = delete_rebalance_entry(db, data_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Data not found")
    return {"data_id": data_id}
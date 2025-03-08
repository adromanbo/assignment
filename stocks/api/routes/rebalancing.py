import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from stocks.core.database import SessionLocal, engine
from stocks.infra.crud import create_rebalance_entry, get_rebalance_list, get_rebalance_entry, delete_rebalance_entry
from stocks.models import Base
from stocks.models.rebalancing import RebalanceData
from stocks.services.rebalancing import rebalancing_service

Base.metadata.create_all(bind=engine)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RebalanceInput(BaseModel):
    start_year: int
    start_month: int
    initial_nav: float
    trading_day: int
    trading_fee: float
    rebalance_month_period: int


class RebalanceOutput(BaseModel):
    data_id: int
    output: dict
    last_rebalance_weight: list


# API Endpoint
@router.post("/rebalance/")
def process_rebalance(data: RebalanceInput):
    """
    리밸런싱 API
    """
    session = SessionLocal()
    try:
        # Run trading strategy (dummy implementation)
        last_rebalance_weight, stats = rebalancing_service.run_rebalancing(
            session,
            data.start_year,
            data.start_month,
            data.initial_nav,
            data.trading_day,
            data.trading_fee,
            data.rebalance_month_period,
        )

        # Save to DB
        investment = RebalanceData(
            start_year=data.start_year,
            start_month=data.start_month,
            initial_capital=data.initial_capital,
            trade_days=[str(d) for d in data.trade_days],
            fee_rate=data.fee_rate,
            rebalance_months=data.rebalance_months,
            rebalance_weights=last_rebalance_weight,
        )
        session.add(investment)
        session.commit()
        session.refresh(investment)

        return RebalanceOutput(data_id=investment.id, output=statistics, last_rebalance_weight=last_rebalance_weight)

    except Exception as e:
        session.rollback()
        logging.error(f"/rebalance/: {traceback.format_exc()}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

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
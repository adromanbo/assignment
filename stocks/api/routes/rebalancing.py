import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from stocks.core.database import SessionLocal, engine, get_db
from stocks.infra.database.rebalancing import rebalancing_repo
from stocks.models import Base
from stocks.models.rebalancing import RebalancingData, serialize_rebalancing_data
from stocks.schemas.rebalancing import *
from stocks.services.rebalancing import rebalancing_service

Base.metadata.create_all(bind=engine)

router = APIRouter()


# API Endpoint
@router.post("/process")
def process_rebalance(data: RebalanceInput):
    """
    리밸런싱 API
    {
        "data_id": 1,
        "output": { "total_return": 0.66,  "cagr": 0.1043, "vol": 0.121, "sharpe": 0.86, "mdd": -0.1947},
        "last_rebalance_weight": [("SPY", 0.5), ("QQQ", 0.5), ... ("BIL", 0)]
    }
    """
    session = SessionLocal()
    try:
        # Run trading strategy (dummy implementation)
        rebalance_weight_list, stats, nav_history = rebalancing_service.run_rebalancing(
            session,
            data.start_year,
            data.start_month,
            data.initial_nav,
            data.trading_day,
            data.trading_fee,
            data.rebalance_month_period,
        )
        print(data.dict())
        # Save to DB
        investment = RebalancingData(
            input_data=data.dict(),
            output_data=stats,
            rebalance_weight_list=rebalance_weight_list,
            nav_history=nav_history,
        )
        session.add(investment)
        session.commit()
        session.refresh(investment)
        print("Asdf")
        return RebalanceProcessOutput(
            data_id=investment.data_id,
            output=stats,
            last_rebalance_weight=rebalance_weight_list[-1],
        )

    except Exception as e:
        session.rollback()
        logging.error(f"/rebalance/: {traceback.format_exc()}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/fetch/all")
def get_rebalancing_all_data(db: Session = Depends(get_db)):
    limit = 200
    entries = serialize_rebalancing_data(rebalancing_repo.fetch_all(db, limit))
    if len(entries) == limit:
        raise HTTPException(status_code=400, detail="Too many entries")
    return GetRebalanceAllDataOutput(data_list=entries)


@router.get("/fetch/{data_id}")
def get_rebalancing_data(data_id: int, db: Session = Depends(get_db)):
    entry = rebalancing_repo.fetch_by_data_id(db, data_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Data not found")
    return GetRebalanceDataOutput(
        input=entry.input_data,
        output=entry.output_data,
        last_rebalance_weight=entry.rebalance_weight_list[-1],
    )


@router.delete("/fetch/{data_id}")
def delete_entry(data_id: int, db: Session = Depends(get_db)):
    entry = rebalancing_repo.delete_by_data_id(db, data_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Data not found")
    return DeleteRebalanceDataOutput(data_id=entry.data_id)

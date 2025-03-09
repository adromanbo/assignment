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
def process_rebalance(data: RebalanceInput) -> RebalanceProcessOutput:
    """
    리밸런싱 API

    params:
    - start_year: int  투자 시작 연도
    - start_month: int  투자 시작 월
    - initial_nav: float  초기 자산가치
    - trading_day: int  거래일
    - trading_fee: float 거래 수수료
    - rebalance_month_period: int  리밸런싱 참고 주기 (월)

    returns:
    - data_id: int
    - output: dict
    - last_rebalance_weight: list
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
def get_rebalancing_all_data(db: Session = Depends(get_db)) -> GetRebalanceAllDataOutput:
    """
    모든 리밸런싱 데이터 조회 API
    좀비 쿼리나 response가 너무 커질 수 있으므로 최대 200개의 데이터만 조회 가능
    returns:
    - data_list: list

    """
    limit = 200
    entries = serialize_rebalancing_data(rebalancing_repo.fetch_all(db, limit))
    if len(entries) == limit:
        raise HTTPException(status_code=400, detail="Too many entries")
    return GetRebalanceAllDataOutput(data_list=entries)


@router.get("/fetch/{data_id}")
def get_rebalancing_data(data_id: int, db: Session = Depends(get_db)) -> GetRebalanceDataOutput:
    """
    리밸런싱 데이터 조회 API
    params:
    - data_id: int

    returns:
    - input: dict
    - output: dict
    - last_rebalance_weight: list
    """
    entry = rebalancing_repo.fetch_by_data_id(db, data_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Data not found")
    return GetRebalanceDataOutput(
        input=entry.input_data,
        output=entry.output_data,
        last_rebalance_weight=entry.rebalance_weight_list[-1],
    )


@router.delete("/fetch/{data_id}")
def delete_entry(data_id: int, db: Session = Depends(get_db)) -> DeleteRebalanceDataOutput:
    """
    리밸런싱 데이터 삭제 API
    params:
    - data_id: int

    returns:
    - data_id: int
    """
    entry = rebalancing_repo.delete_by_data_id(db, data_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Data not found")
    return DeleteRebalanceDataOutput(data_id=entry.data_id)

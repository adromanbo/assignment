from sqlalchemy.orm import Session

from stocks.core.database import SessionLocal
from stocks.services.rebalancing import rebalancing_service

if __name__ == "__main__":
    session: Session = SessionLocal()

    rebalancing_service.run_rebalancing(session, 2020, 1, 1000, 15, 0.001, 3)

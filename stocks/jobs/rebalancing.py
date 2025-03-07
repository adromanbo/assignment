from sqlalchemy.orm import Session

from stocks.core.database import SessionLocal
from stocks.services.rebalancing import run_rebalancing

if __name__ == "__main__":
    session: Session = SessionLocal()

    run_rebalancing(session, 2021, 1, 1000000, 1, 0.001, 6)

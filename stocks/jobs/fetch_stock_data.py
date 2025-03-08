import logging
from sqlalchemy.orm import Session
from stocks.core.database import SessionLocal
from stocks.infra.crud.ticker import create_ticker
from stocks.services.fetch_stock_data import fetch_stock_price, STOCKS, fetch_adjusted_close_price


def update_stock_prices():
    db: Session = SessionLocal()
    for ticker in STOCKS:
        date, close = fetch_adjusted_close_price(ticker)
        create_ticker(db, date, ticker, close)

        print(f"Saved {ticker} - {date}: {close}")
        logging.info(f"Saved {ticker} - {date}: {close}")

    db.close()

if __name__ == "__main__":
    update_stock_prices()
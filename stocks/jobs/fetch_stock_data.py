import requests
from bs4 import BeautifulSoup
from datetime import datetime
from stocks.core.database import engine
from sqlalchemy import text


# DB 세션 설정
def get_db():
    with engine.connect() as conn:
        yield conn


# 야후 파이낸스에서 특정 종목의 가격 가져오기
def fetch_stock_price(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ {ticker} 데이터를 가져오지 못함 (Status Code: {response.status_code})")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    price_span = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})

    if not price_span:
        print(f"⚠️ {ticker} 가격 데이터를 찾을 수 없음")
        return None

    return float(price_span.text.replace(",", ""))


# PostgreSQL에 데이터 저장
def save_to_db(ticker, price):
    today = datetime.now().strftime("%Y-%m-%d")

    db = next(get_db())
    query = text("""
        INSERT INTO daily_ticker (date, ticker, price)
        VALUES (:date, :ticker, :price)
        ON CONFLICT (date, ticker) DO UPDATE
        SET price = EXCLUDED.price
    """)

    db.execute(query, {"date": today, "ticker": ticker, "price": price})
    db.commit()

    print(f"✅ {ticker} 가격 {price} 저장 완료 ({today})")


# 주요 미국 주식 리스트
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ"]


def main():
    print("📢 미국 증시 데이터 업데이트 시작...")
    for ticker in TICKERS:
        price = fetch_stock_price(ticker)
        if price:
            save_to_db(ticker, price)


if __name__ == "__main__":
    main()
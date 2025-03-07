import requests
import datetime

YAHOO_URL = "https://query1.finance.yahoo.com/v7/finance/download/"
STOCKS = ["SPY", "QQQ", "GLD", "TIP"]

def fetch_stock_price(ticker: str) -> (str, float):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        chart = data.get("chart", {}).get("result", [])[0]
        timestamp = chart.get("timestamp", [])[0]
        close_price = chart.get("indicators", {}).get("quote", [])[0].get("close", [])[0]

        date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

        return date, close_price
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")

import requests
import datetime

YAHOO_URL = "https://query1.finance.yahoo.com/v7/finance/download/"
STOCKS = ["SPY", "QQQ", "GLD", "TIP", "BIL"]


def fetch_stock_price(ticker: str, range: int = 1) -> (str, float):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range={range}d"

    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        chart = data.get("chart", {}).get("result", [])[0]
        timestamp = chart.get("timestamp", [])[0]
        close_price = (
            chart.get("indicators", {}).get("quote", [])[0].get("close", [])[0]
        )

        date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

        return date, close_price
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")


def fetch_adjusted_close_price(ticker: str) -> (str, float):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data_list = response.json()
        print(data)
        for data in data_list:
            chart = data.get("chart", {}).get("result", [])[0]
            timestamp = chart.get("timestamp", [])[0]

            # "adjclose" 데이터가 있으면 가져오고, 없으면 기본 "close" 사용
            indicators = chart.get("indicators", {})
            adj_close_price = indicators.get("adjclose", [{}])[0].get("adjclose", [None])[0]
            close_price = indicators.get("quote", [{}])[0].get("close", [None])[0]

            adjusted_price = adj_close_price if adj_close_price is not None else close_price
            date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

        return date, adjusted_price
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")
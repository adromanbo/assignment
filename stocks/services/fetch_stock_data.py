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
    date = datetime.datetime.strptime("2025-02-14", "%Y-%m-%d")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1mo"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
        chart = data.get("chart", {}).get("result", [])[0]
        timestamps = chart.get("timestamp", [])
        indicators = chart.get("indicators", {})

        adj_closes = indicators.get("adjclose", [{}])[0].get("adjclose", [])
        closes = indicators.get("quote", [{}])[0].get("close", [])

        for i, ts in enumerate(timestamps):
            dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            print(dt, date)
            if dt == "2025-02-14":
                adjusted_price = (
                    adj_closes[i] if adj_closes[i] is not None else closes[i]
                )
                return dt, adjusted_price

    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from stocks.api.routes.daily_ticker import router as daily_ticker_router
from stocks.api.routes.rebalancing import router as rebalancing_router
import uvicorn

from stocks.core.middleware import standardize_response_middleware

load_dotenv()

app = FastAPI()
app.middleware("http")(standardize_response_middleware)

app.include_router(daily_ticker_router, prefix="/api/v1/daily_ticker")
app.include_router(rebalancing_router, prefix="/api/v1/rebalancing")

ENV = os.getenv("ENV")


@app.get("/")
def read_root():
    return {
        "status": "success",
        "env": ENV,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
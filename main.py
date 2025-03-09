from fastapi import FastAPI
from stocks.api.routes.daily_ticker import router as daily_ticker_router
from stocks.api.routes.rebalancing import router as rebalancing_router
import uvicorn

app = FastAPI()

app.include_router(daily_ticker_router, prefix="/daily_ticker")
app.include_router(rebalancing_router, prefix="/rebalancing")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
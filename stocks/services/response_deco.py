import traceback

from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse

from stocks.schemas.standard import StandardResponse

from functools import wraps
from typing import Callable, Any
import inspect

app = FastAPI()
router = APIRouter()


def standardize_response(func: Callable) -> Callable:
    if inspect.iscoroutinefunction(func):
        # 비동기 함수인 경우
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                return StandardResponse(status="success", data=result, error=None)
            except Exception as e:
                print(traceback.format_exc())

                return JSONResponse(
                    content={
                        "status": "error",
                        "data": None,
                        "error": {"message": str(e)},
                    },
                    status_code=500,
                )

        return async_wrapper
    else:
        # 동기 함수인 경우
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                return StandardResponse(status="success", data=result, error=None)
            except Exception as e:
                print(traceback.format_exc())
                return JSONResponse(
                    content={
                        "status": "error",
                        "data": None,
                        "error": {"message": str(e)},
                    },
                    status_code=500,
                )

        return sync_wrapper

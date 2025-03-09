import json

from fastapi import Request
from fastapi.responses import JSONResponse

async def standardize_response_middleware(request: Request, call_next: callable):
    """
    같은 형식의 응답을 보내기 위한 미들웨어
    """
    response = await call_next(request)

    body = b"".join([chunk async for chunk in response.body_iterator])

    try:
        content = json.loads(body.decode("utf-8"))
    except Exception:
        return response

    return JSONResponse(content={"status": "success", "data": content}, status_code=response.status_code)

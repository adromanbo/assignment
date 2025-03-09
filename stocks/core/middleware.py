import json

from fastapi import Request
from fastapi.responses import JSONResponse

async def standardize_response_middleware(request: Request, call_next):
    response = await call_next(request)

    # 응답 내용을 읽기 위해 response.body_iterator 사용
    body = b"".join([chunk async for chunk in response.body_iterator])

    try:
        content = json.loads(body.decode("utf-8"))
    except Exception:
        return response  # JSON 변환 실패 시 원래 응답 반환

    return JSONResponse(content={"status": "success", "data": content}, status_code=response.status_code)

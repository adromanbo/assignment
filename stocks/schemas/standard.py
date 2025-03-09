from typing import Generic, TypeVar, Optional

from pydantic.v1.generics import GenericModel

T = TypeVar("T")  # 제네릭 타입 변수

class StandardResponse(GenericModel, Generic[T]):
    status: str  # "success" 또는 "error"
    data: Optional[T] = None  # 실제 데이터 (제네릭)
    error: Optional[dict] = None  # 에러 메시지
    class Config:
        arbitrary_types_allowed = True
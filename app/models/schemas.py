from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Pertanyaan analitik pariwisata/perhotelan dalam Bahasa Indonesia.",
    )


class SQLResponse(BaseModel):
    status: Literal["success", "cached", "error"]
    sql_query: str
    data: list[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    source: Literal["llm", "cache", "chat"]
    intent: Optional[str] = None
    answer: Optional[str] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_code: str
    message: str
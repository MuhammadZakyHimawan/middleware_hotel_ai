import asyncpg
from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ErrorResponse, QuestionRequest, SQLResponse
from app.services.orchestrator import Orchestrator
from app.utils.sql_sanitizer import SQLSanitizationError

router = APIRouter()


@router.post(
    "/v1/ask",
    response_model=SQLResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def ask_question(payload: QuestionRequest, request: Request) -> SQLResponse:
    pool: asyncpg.Pool = request.app.state.pool
    orchestrator = Orchestrator(pool)

    try:
        result = await orchestrator.run_pipeline(payload.question)
    except SQLSanitizationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "SQL_SANITIZATION_FAILED", "message": str(e)},
        ) from e
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "SQL_EXECUTION_FAILED",
                "message": f"Eksekusi query ke PostgreSQL gagal: {e}",
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"Proses pipeline gagal: {e}",
            },
        ) from e

    return SQLResponse(
        status=result["status"],
        sql_query=result["sql_query"],
        data=result["data"],
        row_count=result["row_count"],
        source=result["source"],
        intent=result.get("intent"),
        answer=result.get("answer"),
    )


@router.get("/health", include_in_schema=False)
async def health_check(request: Request) -> dict[str, str]:
    return {"status": "ok"}
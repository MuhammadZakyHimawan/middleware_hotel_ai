import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import asyncpg

from app.config import get_settings
from app.services.context_mapper import Intent, get_context
from app.services.llm_client import LLMClient, LLMClientError
from app.utils.sql_sanitizer import sanitize_sql

logger = logging.getLogger(__name__)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Tipe tidak bisa di-serialize ke JSON: {type(obj).__name__}")

CACHE_LOOKUP_SQL = """
SELECT sql_query, sql_result::text
FROM log_pertanyaan
WHERE question = $1
ORDER BY created_at DESC
LIMIT 1;
"""

CACHE_INSERT_SQL = """
INSERT INTO log_pertanyaan (question, sql_query, sql_result, intent_detected)
VALUES ($1, $2, $3::jsonb, $4)
ON CONFLICT (question) DO NOTHING;
"""


class Orchestrator:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._llm = LLMClient()

    async def run_pipeline(self, question: str) -> dict[str, Any]:
        settings = get_settings()

        intent, ddl_context = get_context(question)

        if settings.LLM_CHAT_ONLY:
            answer = await self._llm.chat_answer(question)
            return {
                "status": "success",
                "source": "chat",
                "intent": intent.value,
                "sql_query": "",
                "data": [],
                "row_count": 0,
                "answer": answer,
            }

        # cached = await self._lookup_cache(question)
        # if cached is not None:
        #     sql_query, sql_result_text = cached
        #     data = json.loads(sql_result_text)
        #     return {
        #         "status": "success",
        #         "source": "cache",
        #         "intent": None,
        #         "sql_query": sql_query,
        #         "data": data,
        #         "row_count": len(data),
        #     }

        if intent == Intent.UNKNOWN:
            answer = await self._llm.chat_answer(question)
            return {
                "status": "success",
                "source": "chat",
                "intent": intent.value,
                "sql_query": "",
                "data": [],
                "row_count": 0,
                "answer": answer,
            }

        raw_sql = await self._llm.call_llm(question, ddl_context)

        clean_sql = sanitize_sql(raw_sql)

        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction(readonly=True):
                    rows = await conn.fetch(clean_sql)
        except asyncpg.PostgresError as e:
            raise asyncpg.PostgresError(
                f"Eksekusi query gagal: {e}"
            ) from e

        data = [dict(row) for row in rows]

        await self._save_to_cache(question, clean_sql, data, intent.value)

        answer = None
        if settings.GUARDRAILS_ENABLED and data:
            try:
                answer = await self._llm.summarize_result(
                    question, clean_sql, data, intent.value
                )
            except LLMClientError as e:
                logger.warning(
                    "Generasi jawaban dari hasil query gagal (dilewati): %s", e
                )

        return {
            "status": "success",
            "source": "llm",
            "intent": intent.value,
            "sql_query": clean_sql,
            "data": data,
            "row_count": len(data),
            "answer": answer,
        }

    async def _lookup_cache(self, question: str) -> tuple[str, str] | None:
        try:
            row = await self._pool.fetchrow(CACHE_LOOKUP_SQL, question)
        except asyncpg.PostgresError as e:
            logger.warning("Lookup cache gagal (dilewati): %s", e)
            return None
        if row is None:
            return None
        return row["sql_query"], row["sql_result"]

    async def _save_to_cache(
        self,
        question: str,
        sql_query: str,
        data: list[dict[str, Any]],
        intent: str,
    ) -> None:
        try:
            await self._pool.execute(
                CACHE_INSERT_SQL,
                question,
                sql_query,
                json.dumps(data, default=_json_default),
                intent,
            )
        except asyncpg.PostgresError as e:
            logger.warning("Penyimpanan cache gagal (dilewati): %s", e)
import argparse
import asyncio
import logging

from app.services.context_mapper import get_context
from app.services.llm_client import LLMClient, LLMClientError
from app.utils.sql_sanitizer import SQLSanitizationError, sanitize_sql

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

SAMPLE_QUESTIONS = [
    "Berapa rata-rata harga hotel bintang 4?",
    "Berapa tingkat penghunian kamar (TPK) pada bulan Mei 2025?",
    "Jumlah kunjungan wisatawan mancanegara dari China tahun 2025",
    "Daftar reviews hotel yang ratingnya 1 bintang",
    "Berapa inflasi Jakarta bulan Januari 2025?",
]

SAMPLE_CHAT_QUESTIONS = [
    "Sekarang hari apa?",
    "Apa itu TPK dalam pariwisata?",
    "Siapa presiden Indonesia sekarang?",
    "Apa ibukota Jerman?",
]


async def test_one(question: str) -> None:
    intent, ddl_context = get_context(question)
    print("=" * 70)
    print(f"PERTANYAAN : {question}")
    print(f"INTENT     : {intent.value}")
    print("-" * 70)

    llm = LLMClient()
    raw_sql = await llm.call_llm(question, ddl_context)
    print("SQL MENTAH DARI LLM:")
    print(raw_sql)
    print("-" * 70)

    clean_sql = sanitize_sql(raw_sql)
    print("SQL SETELAH SANITIZE:")
    print(clean_sql)
    print("-" * 70)
    print("=> LLM OK: menghasilkan SQL valid TANPA menyentuh database.")
    print("=" * 70)


async def test_chat(question: str) -> None:
    print("=" * 70)
    print(f"PERTANYAAN : {question}")
    print("-" * 70)

    llm = LLMClient()
    answer = await llm.chat_answer(question)
    print("JAWABAN LLM (chat):")
    print(answer)
    print("=" * 70)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tes AI middleware Text-to-SQL TANPA akses database."
    )
    parser.add_argument(
        "--sql",
        action="store_true",
        help="Tes jalur SQL (intent -> SQL -> sanitize), tanpa DB.",
    )
    parser.add_argument(
        "questions",
        nargs="*",
        help="Pertanyaan (boleh lebih dari satu); default memakai contoh.",
    )
    args = parser.parse_args()

    if args.sql:
        questions = args.questions or SAMPLE_QUESTIONS
        for q in questions:
            try:
                await test_one(q)
            except LLMClientError as e:
                print(f"!! LLM ERROR: {e}")
            except SQLSanitizationError as e:
                print(f"!! SANITIZE ERROR: {e}")
            except Exception as e:
                print(f"!! ERROR ({type(e).__name__}): {e}")
        return

    questions = args.questions or SAMPLE_CHAT_QUESTIONS
    for q in questions:
        try:
            await test_chat(q)
        except LLMClientError as e:
            print(f"!! LLM ERROR: {e}")
        except Exception as e:
            print(f"!! ERROR ({type(e).__name__}): {e}")


if __name__ == "__main__":
    asyncio.run(main())
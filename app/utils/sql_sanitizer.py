import sqlglot
import sqlglot.expressions as exp
from sqlglot.errors import SqlglotError

ALLOWED_TABLES = frozenset(
    {
        "asal_turis",
        "event_agenda",
        "event_unik",
        "fact_harga_hotel",
        "fact_inflasi",
        "fact_review_hotel",
        "fact_tpk",
        "fact_wisman_pintu_masuk",
        "fact_wisnus_tujuan",
        "fakta_kurs_harian",
        "hari_libur",
        "hotel_master",
        "jenis_transportasi",
        "kode_mata_uang",
        "lama_menginap",
        "pemetaan_rute_halte",
        "rute_angkutan",
        "titik_berhenti",
    }
)

FORBIDDEN_STATEMENT_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Merge,
    exp.Command,
)

AGGREGATE_FUNC_TYPES = (exp.AggFunc, exp.Count, exp.Sum, exp.Avg, exp.Max, exp.Min)


class SQLSanitizationError(Exception):
    pass


def _strip_sql_fences(raw_sql: str) -> str:
    text = raw_sql.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _enforce_limit(select: exp.Select) -> None:
    if select.args.get("limit") is None:
        select.set("limit", exp.Limit(expression=exp.Literal.number(100)))


def _is_aggregate_query(select: exp.Select) -> bool:
    if select.args.get("group"):
        return True
    if select.args.get("having"):
        return True
    if select.args.get("distinct"):
        return True
    for node in select.walk():
        if isinstance(node, AGGREGATE_FUNC_TYPES):
            return True
    return False


def _validate_tables(select: exp.Select) -> None:
    referenced = set()
    for table in select.find_all(exp.Table):
        name = (table.name or "").split(".")[-1].lower()
        if name:
            referenced.add(name)
    unknown = referenced - ALLOWED_TABLES
    if unknown:
        listed = ", ".join(sorted(unknown))
        raise SQLSanitizationError(
            f"Tabel tidak diizinkan dalam whitelist: {listed}"
        )


def sanitize_sql(raw_sql: str) -> str:
    if not isinstance(raw_sql, str) or not raw_sql.strip():
        raise SQLSanitizationError("Output LLM kosong atau bukan string SQL.")

    clean_text = _strip_sql_fences(raw_sql)

    try:
        parsed = sqlglot.parse(clean_text, read="postgres")
    except SqlglotError as e:
        raise SQLSanitizationError(f"SQL tidak dapat di-parse oleh sqlglot: {e}") from e

    statements = [stmt for stmt in parsed if stmt is not None]
    if not statements:
        raise SQLSanitizationError("Tidak ditemukan statement SQL yang valid.")

    if len(statements) > 1:
        raise SQLSanitizationError(
            "Multi-statement terdeteksi; hanya satu perintah SELECT yang diizinkan."
        )

    statement = statements[0]

    if isinstance(statement, FORBIDDEN_STATEMENT_TYPES):
        raise SQLSanitizationError(
            f"Statement terlarang: {statement.__class__.__name__.lower()}. "
            "Hanya perintah SELECT yang diperbolehkan."
        )

    if not isinstance(statement, exp.Select):
        raise SQLSanitizationError(
            f"Statement tidak dikenali: {statement.__class__.__name__}. "
            "Hanya perintah SELECT yang diperbolehkan."
        )

    if not _is_aggregate_query(statement):
        _enforce_limit(statement)

    _validate_tables(statement)

    try:
        return statement.sql(dialect="postgres")
    except SqlglotError as e:
        raise SQLSanitizationError(f"Transpilasi SQL gagal: {e}") from e
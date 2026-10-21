import logging
import re

GUARDRAIL_FALLBACK = (
    "Maaf, saya tidak dapat menampilkan jawaban tersebut. "
    "Silakan ajukan pertanyaan lain seputar pariwisata dan perhotelan DKI Jakarta."
)

_TOXIC_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\banjing\b",
        r"\bbangsat\b",
        r"\bbajingan\b",
        r"\bbrengsek\b",
        r"\bgoblok\b",
        r"\btolol\b",
        r"\bidiot\b",
        r"\bkampret\b",
        r"\bkontol\b",
        r"\bmemek\b",
        r"\bngewe\b",
        r"\bngentot\b",
        r"\bjancok\b",
        r"\basu\b",
        r"\bbabi\b",
        r"\bkampang\b",
        r"\bpukimak\b",
        r"\bpeler\b",
        r"\bpelir\b",
        r"\bsialan\b",
        r"\bsange\b",
        r"\bfuck\b",
        r"\bfucking\b",
        r"\bshit\b",
        r"\bbitch\b",
        r"\bbastard\b",
        r"\basshole\b",
        r"\bcunt\b",
        r"\bdickhead\b",
        r"\bmotherfucker\b",
        r"\bnigger\b",
        r"\bnigga\b",
        r"\bretard\b",
        r"\bwhore\b",
        r"\bslut\b",
        r"cara membuat bom",
        r"resep bom",
        r"pembuatan bom",
        r"bahan peledak",
        r"meledakkan",
        r"membuat racun",
        r"membuat (?:kokain|sabu|narkoba|metamfetamin)",
        r"cara bunuh diri",
        r"mengakhiri hidup",
        r"cara membunuh",
        r"cara menghabisi",
    ]
]

_PII_PATTERNS = [
    re.compile(p)
    for p in [
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        r"(?<!\d)(?:\+?62|0)8[1-9][0-9]{7,11}(?!\d)",
        r"\b\d{16}\b",
        r"\b\d{2}[.\s-]\d{3}[.\s-]\d{3}[.\s-]\d[.\s-]\d{3}[.\s-]\d{3}\b",
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    ]
]

_SQL_PATTERN = re.compile(r"\bSELECT\b.{0,300}?\bFROM\b", re.IGNORECASE | re.DOTALL)

_LEAK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"jangan ikuti",
        r"abaikan",
        r"ignore (?:all )?(?:previous|prior|the above)",
        r"disregard",
        r"override",
        r"(?:instruksi|perintah) (?:sebelumnya|sistem)",
        r"system prompt",
        r"sistem prompt",
        r"kamu (?:adalah|sekarang menjadi|berperan)",
        r"anda (?:adalah|berperan)",
        r"rule (?:number|no\.?)\s*\d+",
        r"forget (?:your )?(?:instructions|rules|guidelines)",
        r"(?m)(?:^|\n)\s*(?:user|system|assistant)\s*:\s*",
    ]
]

_DOMAIN_KEYWORDS = (
    "pariwisata",
    "wisata",
    "wisatawan",
    "wisman",
    "wisnus",
    "turis",
    "travel",
    "destinasi",
    "hotel",
    "perhotelan",
    "akomodasi",
    "kamar",
    "okupansi",
    "tpk",
    "hunian",
    "bintang",
    "review",
    "ulasan",
    "rating",
    "kepuasan",
    "menginap",
    "lama menginap",
    "jakarta",
    "dkj",
    "inflasi",
    "kurs",
    "rupiah",
    "dollar",
    "mata uang",
    "bank indonesia",
    "hari libur",
    "libur panjang",
    "cuti bersama",
    "event",
    "agenda",
    "kunjungan",
    "pintu masuk",
    "negara asal",
    "harga",
    "tarif",
    "lead time",
    "transportasi",
    "angkutan",
    "jxb",
    "jakarta tourism analytics",
)

_OFFTOPIC_RED_FLAG_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"resep|masak|masakan|bumbu|\bsdt\b|\bsdm\b|tambahkan|\boven\b",
        r"dosis|obat|gejala|demam|konsumsi obat",
        r"presiden|pemilu|pemilihan|partai politik|menteri|kabinet|siapa presiden",
        r"pacaran|berpacaran|perasaan (?:aku|saya|dia)|hubungan asmara",
        r"membuat (?:aplikasi|website|program|game)|\btugas (?:kuliah|sekolah)\b|skripsi|koding|\bprogramming\b",
        r"\bdef\s+\w+\s*\(|\bclass\s+\w+|\bimport\s+\w+",
        r"kipas angin|servis (?:tv|kipas|ac)|perbaikan (?:tv|kipas|ac)",
    ]
]

_URL_PATTERNS = [
    re.compile(r"(?:https?|ftp)://[^\s<>\"']+"),
    re.compile(r"\bwww\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\[[^\]]*\]\([^)]+\)"),
    re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"),
]


def _hits_patterns(text: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def _is_off_topic(text: str) -> bool:
    lowered = text.lower()
    domain_hits = sum(1 for kw in _DOMAIN_KEYWORDS if kw in lowered)
    if domain_hits >= 1:
        return False
    return _hits_patterns(lowered, _OFFTOPIC_RED_FLAG_PATTERNS)


def check_guardrails(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    violations: list[str] = []
    if _hits_patterns(text, _TOXIC_PATTERNS):
        violations.append("TOXIC")
    if _hits_patterns(text, _PII_PATTERNS):
        violations.append("PII")
    if _hits_patterns(text, _LEAK_PATTERNS) or _SQL_PATTERN.search(text):
        violations.append("PROMPT_LEAK")
    if _is_off_topic(text):
        violations.append("OFF_TOPIC")
    if _hits_patterns(text, _URL_PATTERNS):
        violations.append("EXTERNAL_URL")
    return violations


def enforce_guardrails(
    text: str, logger: logging.Logger | None = None
) -> str:
    violations = check_guardrails(text)
    if not violations:
        return text
    if logger is not None:
        logger.warning(
            "Jawaban diblokir guardrail (%s): %.200s",
            ", ".join(violations),
            text,
        )
    return GUARDRAIL_FALLBACK
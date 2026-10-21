from enum import Enum
from typing import Tuple

DDL = {
    "hotel_master": """CREATE TABLE public.hotel_master (
    id_kompetitor varchar(10) NOT NULL PRIMARY KEY,
    nama_hotel text,
    kelas_bintang bigint,
    total_kamar integer,
    fasilitas text,
    alamat text,
    kota text,
    latitude double precision,
    longitude double precision
);""",
    "fact_harga_hotel": """CREATE TABLE public.fact_harga_hotel (
    id_harga varchar(100) NOT NULL PRIMARY KEY,
    id_kompetitor varchar(10) NOT NULL REFERENCES public.hotel_master(id_kompetitor) ON DELETE CASCADE,
    scrape_date date NOT NULL,
    checkin_date date NOT NULL,
    lead_time integer NOT NULL,
    harga bigint,
    sumber varchar(100),
    created_at timestamp DEFAULT now()
);""",
    "fact_review_hotel": """CREATE TABLE public.fact_review_hotel (
    id_review varchar(64) NOT NULL PRIMARY KEY,
    id_kompetitor varchar(10) REFERENCES public.hotel_master(id_kompetitor),
    nama_reviewer varchar(255),
    rating_bintang smallint,
    isi_review text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    tahun integer NOT NULL,
    bulan integer NOT NULL
);""",
    "fact_tpk": """CREATE TABLE public.fact_tpk
    id integer NOT NULL PRIMARY KEY,
    klasifikasi_bintang integer NOT NULL,
    tpk_persen numeric(6,1) NOT NULL,
    tahun integer NOT NULL,
    bulan integer NOT NULL
);""",
    "asal_turis": """CREATE TABLE public.asal_turis (
    id integer NOT NULL PRIMARY KEY,
    tahun integer NOT NULL,
    bulan integer NOT NULL,
    negara_asal varchar(100) NOT NULL,
    jumlah_kunjungan bigint NOT NULL
);""",
    "fact_wisman_pintu_masuk": """CREATE TABLE public.fact_wisman_pintu_masuk (
    id integer NOT NULL PRIMARY KEY,
    tempat varchar(255),
    jumlah_kunjungan integer,
    tahun integer NOT NULL,
    bulan integer NOT NULL
);""",
    "fact_wisnus_tujuan": """CREATE TABLE public.fact_wisnus_tujuan (
    id integer NOT NULL PRIMARY KEY,
    tempat varchar(255),
    jumlah_perjalanan integer,
    tahun integer NOT NULL,
    bulan integer NOT NULL
);""",
    "lama_menginap": """CREATE TABLE public.lama_menginap (
    id integer NOT NULL PRIMARY KEY,
    tahun integer NOT NULL,
    bulan integer,
    jenis_wisatawan varchar(30),
    lama_menginap_hari numeric
);""",
    "fact_inflasi": """CREATE TABLE public.fact_inflasi (
    id integer NOT NULL PRIMARY KEY,
    tahun integer NOT NULL,
    bulan integer NOT NULL,
    tempat varchar(100),
    nilai_inflasi double precision
);""",
    "fakta_kurs_harian": """CREATE TABLE public.fakta_kurs_harian (
    id_kurs integer NOT NULL PRIMARY KEY,
    id_mata_uang integer NOT NULL REFERENCES public.kode_mata_uang(id) ON DELETE CASCADE,
    tanggal date NOT NULL,
    nilai_satuan numeric(10,2),
    kurs_beli numeric(15,2),
    kurs_jual numeric(15,2),
    kurs_tengah numeric(15,2)
);""",
    "kode_mata_uang": """CREATE TABLE public.kode_mata_uang (
    id integer NOT NULL PRIMARY KEY,
    kode varchar(10),
    nama_mata_uang varchar(100)
);""",
    "hari_libur": """CREATE TABLE public.hari_libur (
    tanggal date NOT NULL PRIMARY KEY,
    is_weekend boolean,
    is_libur_nasional boolean,
    is_cuti_bersama boolean,
    is_libur_sekolah boolean,
    is_kejepit boolean,
    is_libur_panjang boolean,
    total_hari_beruntun integer,
    keterangan varchar(255)
);""",
    "event_agenda": """CREATE TABLE public.event_agenda (
    id_event varchar(32) NOT NULL PRIMARY KEY,
    sumber varchar(50) NOT NULL,
    judul text NOT NULL,
    tanggal_mulai date,
    tanggal_akhir date,
    lokasi_venue text,
    kategori text,
    url_detail text,
    url_gambar text,
    deskripsi text,
    tanggal_unggah date,
    scraped_at timestamp DEFAULT now()
);""",
    "event_unik": """CREATE VIEW public.event_unik AS
SELECT DISTINCT ON (judul, tanggal_mulai) id_event, sumber, judul,
tanggal_mulai, tanggal_akhir, lokasi_venue, kategori, url_detail,
url_gambar, deskripsi, tanggal_unggah, scraped_at,
array_agg(sumber) OVER (PARTITION BY judul, tanggal_mulai) AS sumber_lain
FROM public.event_agenda
ORDER BY judul, tanggal_mulai,
CASE sumber WHEN 'jiexpo' THEN 1 WHEN 'ice' THEN 2 WHEN 'nice' THEN 3
WHEN 'jcc' THEN 4 WHEN 'jakarta.go.id' THEN 5 WHEN 'eventbrite' THEN 6 ELSE 99 END;""",
    "dim_destinasi": """CREATE TABLE public.dim_destinasi (
    id_destinasi integer NOT NULL PRIMARY KEY,
    nama_destinasi text NOT NULL,
    kategori varchar(100),
    latitude numeric,
    longitude numeric,
    alamat text,
    kelurahan varchar(100),
    kecamatan varchar(100),
    kota varchar(100)
);""",
}

INTENT_DEFINITIONS = [
    (
        "HOTEL_PRICING",
        {
            "keyword": [
                "harga",
                "price",
                "tarif",
                "rate",
                "murah",
                "mahal",
                "kompetitor",
                "booking",
                "pesan kamar",
                "sewa",
                "lead time",
            ],
            "tables": ("hotel_master", "fact_harga_hotel"),
            "domain": "perhotelan",
        },
    ),
    (
        "OCCUPANCY_RATE",
        {
            "keyword": [
                "tpk",
                "okupansi",
                "hunian",
                "occupancy",
                "tingkat penghunian",
                "utilisasi kamar",
                "kamar terisi",
            ],
            "strong": ["tpk", "okupansi", "hunian", "occupancy", "tingkat penghunian"],
            "tables": ("fact_tpk",),
            "domain": "statistik perhotelan",
        },
    ),
    (
        "HOTEL_REVIEW",
        {
            "keyword": [
                "review",
                "rating",
                "ulasan",
                "bintang",
                "komentar",
                "satisfaksi",
                "kepuasan",
                "pelanggan",
                "rekomendasi hotel",
            ],
            "strong": ["review", "ulasan", "kepuasan", "satisfaksi"],
            "tables": ("hotel_master", "fact_review_hotel"),
            "domain": "perhotelan",
        },
    ),
    (
        "TOURIST_ARRIVAL",
        {
            "keyword": [
                "turis",
                "wisman",
                "wisatawan asing",
                "kunjungan",
                "pintu masuk",
                "negara asal",
                "arrival",
                "kedatangan",
                "mancanegara",
            ],
            "tables": ("asal_turis", "fact_wisman_pintu_masuk"),
            "domain": "pariwisata",
        },
    ),
    (
        "DOMESTIC_TOURISM",
        {
            "keyword": [
                "wisnus",
                "wisatawan domestik",
                "tujuan",
                "lama menginap",
                "menginap",
                "perjalanan",
                "nusantara",
            ],
            "tables": ("fact_wisnus_tujuan", "lama_menginap"),
            "domain": "pariwisata domestik",
        },
    ),
    (
        "ECONOMIC_CONTEXT",
        {
            "keyword": [
                "inflasi",
                "kurs",
                "rupiah",
                "dollar",
                "mata uang",
                "ekonomi",
                "nilai tukar",
                "bi",
                "bank indonesia",
                "hari libur",
                "libur panjang",
                "cuti bersama",
            ],
            "tables": ("fact_inflasi", "fakta_kurs_harian", "kode_mata_uang", "hari_libur"),
            "domain": "indikator ekonomi",
        },
    ),
    (
        "DESTINATION_TOURISM",
        {
            "keyword": [
                "destinasi",
                "wisata",
                "tempat wisata",
                "objek wisata",
                "museum",
                "taman",
                "pantai",
                "monumen",
                "lokasi",
                "alamat",
                "koordinat",
                "latitude",
                "longitude",
            ],
            "tables": ("dim_destinasi",),
            "domain": "pariwisata destinasi",
        },
    ),
]


class Intent(str, Enum):
    HOTEL_PRICING = "HOTEL_PRICING"
    HOTEL_REVIEW = "HOTEL_REVIEW"
    OCCUPANCY_RATE = "OCCUPANCY_RATE"
    TOURIST_ARRIVAL = "TOURIST_ARRIVAL"
    DOMESTIC_TOURISM = "DOMESTIC_TOURISM"
    ECONOMIC_CONTEXT = "ECONOMIC_CONTEXT"
    DESTINATION_TOURISM = "DESTINATION_TOURISM"
    UNKNOWN = "UNKNOWN"


def _score_keywords(prompt: str, config: dict) -> int:
    lowered = prompt.lower()
    score = 0
    for i, kw in enumerate(config["keyword"]):
        if kw in lowered:
            score += 2 if kw in config.get("strong", ()) else 1
    return score


def detect_intent(question: str) -> Tuple[Intent, tuple[str, ...]]:
    candidates: list[tuple[int, int, str, tuple[str, ...]]] = []
    for index, (intent_key, config) in enumerate(INTENT_DEFINITIONS):
        score = _score_keywords(question, config)
        if score > 0:
            candidates.append((score, index, intent_key, config["tables"]))

    if not candidates:
        return Intent.UNKNOWN, tuple(DDL.keys())

    candidates.sort(key=lambda c: (-c[0], c[1]))
    _, _, intent_key, tables = candidates[0]
    return Intent(intent_key), tables


def build_ddl_context(tables: tuple[str, ...]) -> str:
    available = [t for t in tables if t in DDL]
    return "\n\n".join(DDL[t] for t in available)


def get_context(question: str) -> Tuple[Intent, str]:
    intent, tables = detect_intent(question)
    return intent, build_ddl_context(tables)
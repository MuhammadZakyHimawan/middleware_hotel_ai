-- Migration: tabel dim_destinasi untuk data destinasi wisata
-- Skema: public

CREATE TABLE IF NOT EXISTS public.dim_destinasi (
    id_destinasi integer NOT NULL PRIMARY KEY,
    nama_destinasi text NOT NULL,
    kategori varchar(100),
    latitude numeric,
    longitude numeric,
    alamat text,
    kelurahan varchar(100),
    kecamatan varchar(100),
    kota varchar(100)
);

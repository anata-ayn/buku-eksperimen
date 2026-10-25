from datetime import datetime
from decimal import Decimal


def angka(nilai):
    if nilai is None:
        return None
    if isinstance(nilai, Decimal):
        return float(nilai)
    return nilai


def waktu(nilai):
    if nilai is None:
        return None
    if isinstance(nilai, datetime):
        return nilai.replace(microsecond=0).isoformat() + "Z"
    return str(nilai).replace(" ", "T") + "Z"


def proyek(row):
    return {
        "id": row["id"],
        "nama": row["nama"],
        "deskripsi": row["deskripsi"],
        "target_f1": angka(row["target_f1"]),
        "dibuat_pada": waktu(row["dibuat_pada"]),
    }


def ringkasan_proyek(row):
    data = proyek(row)
    data["jumlah_percobaan"] = int(row["jumlah"] or 0)
    data["f1_terbaik"] = angka(row["f1_terbaik"])
    return data


def percobaan(row):
    return {
        "id": row["id"],
        "proyek_id": row["proyek_id"],
        "nama": row["nama"],
        "tahap": row["tahap"],
        "model": row["model"],
        "f1_macro": angka(row["f1_macro"]),
        "accuracy": angka(row["accuracy"]),
        "invalid_count": int(row["invalid_count"]),
        "n_data": int(row["n_data"]),
        "waktu_detik": angka(row["waktu_detik"]),
        "catatan": row["catatan"],
        "dicatat_pada": waktu(row["dicatat_pada"]),
    }

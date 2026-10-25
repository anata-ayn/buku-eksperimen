class ValidationError(ValueError):
    pass


def _text(data, key, maks, wajib=False, label=None):
    label = label or key
    nilai = data.get(key, "")
    if nilai is None:
        nilai = ""
    if not isinstance(nilai, str):
        raise ValidationError(f"{label} harus berupa teks.")
    nilai = nilai.strip()
    if wajib and not nilai:
        raise ValidationError(f"{label} wajib diisi.")
    if len(nilai) > maks:
        raise ValidationError(f"{label} maksimal {maks} karakter (sekarang {len(nilai)}).")
    return nilai


def _angka(data, key, label, minimum, maksimum, wajib=True):
    mentah = data.get(key)
    if mentah is None or (isinstance(mentah, str) and not mentah.strip()):
        if wajib:
            raise ValidationError(f"{label} wajib diisi.")
        return None
    if isinstance(mentah, bool):
        raise ValidationError(f"{label} harus berupa angka.")
    if isinstance(mentah, str):
        mentah = mentah.strip().replace(",", ".")
    try:
        nilai = float(mentah)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} harus berupa angka, misalnya 0,8329.")
    if nilai != nilai or nilai in (float("inf"), float("-inf")):
        raise ValidationError(f"{label} harus berupa angka biasa.")
    if nilai < minimum or nilai > maksimum:
        raise ValidationError(f"{label} harus di antara {minimum:g} dan {maksimum:g}.")
    return nilai


def _bulat(data, key, label, minimum, maksimum):
    nilai = _angka(data, key, label, minimum, maksimum)
    if nilai != int(nilai):
        raise ValidationError(f"{label} harus bilangan bulat.")
    return int(nilai)


def validasi_proyek(data):
    if not isinstance(data, dict):
        raise ValidationError("Isi permintaan harus berupa objek JSON.")
    return {
        "nama": _text(data, "nama", 80, wajib=True, label="Nama buku"),
        "deskripsi": _text(data, "deskripsi", 400, label="Deskripsi"),
        "target_f1": _angka(data, "target_f1", "Target F1", 0, 1, wajib=False),
    }


def validasi_percobaan(data):
    if not isinstance(data, dict):
        raise ValidationError("Isi permintaan harus berupa objek JSON.")
    tahap = _text(data, "tahap", 20, wajib=True, label="Tahap")
    if tahap not in ("validasi", "test"):
        raise ValidationError("Tahap harus 'validasi' atau 'test'.")
    n_data = _bulat(data, "n_data", "Jumlah data", 1, 1_000_000)
    invalid = _bulat(data, "invalid_count", "Jumlah invalid", 0, 1_000_000)
    if invalid > n_data:
        raise ValidationError("Jumlah invalid tidak boleh lebih besar dari jumlah data.")
    return {
        "nama": _text(data, "nama", 120, wajib=True, label="Nama percobaan"),
        "tahap": tahap,
        "model": _text(data, "model", 120, label="Model"),
        "f1_macro": _angka(data, "f1_macro", "F1 macro", 0, 1),
        "accuracy": _angka(data, "accuracy", "Akurasi", 0, 1),
        "invalid_count": invalid,
        "n_data": n_data,
        "waktu_detik": _angka(data, "waktu_detik", "Waktu", 0, 10_000_000, wajib=False),
        "catatan": _text(data, "catatan", 1000, label="Catatan"),
    }


def validasi_catatan(data):
    if not isinstance(data, dict):
        raise ValidationError("Isi permintaan harus berupa objek JSON.")
    return _text(data, "catatan", 1000, label="Catatan")

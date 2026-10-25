import hmac

from flask import Blueprint, current_app, jsonify, request

from . import serialize
from .validate import ValidationError, validasi_catatan, validasi_percobaan, validasi_proyek

api = Blueprint("api", __name__)


def db():
    return current_app.extensions["db"]


def galat(pesan, status):
    return jsonify({"error": pesan}), status


def kunci_tulis_valid():
    kunci = current_app.config["EDIT_KEY"]
    if not kunci:
        return True
    kiriman = request.headers.get("X-Edit-Key", "")
    return hmac.compare_digest(kiriman.encode(), kunci.encode())


@api.before_request
def jaga_penulisan():
    if request.method in ("POST", "PATCH", "DELETE") and not kunci_tulis_valid():
        return galat("Kunci tulis salah atau belum diisi. Masukkan kunci yang ada di file .env (EDIT_KEY).", 401)


@api.errorhandler(ValidationError)
def tolak_input(exc):
    return galat(str(exc), 400)


@api.get("/status")
def status():
    return jsonify({"tulis_terkunci": bool(current_app.config["EDIT_KEY"])})


@api.get("/proyek")
def daftar_proyek():
    rows = db().query(
        """
        SELECT p.id, p.nama, p.deskripsi, p.target_f1, p.dibuat_pada,
               COUNT(r.id) AS jumlah, MAX(r.f1_macro) AS f1_terbaik
        FROM proyek p
        LEFT JOIN percobaan r ON r.proyek_id = p.id
        GROUP BY p.id, p.nama, p.deskripsi, p.target_f1, p.dibuat_pada
        ORDER BY p.id
        """
    )
    return jsonify([serialize.ringkasan_proyek(r) for r in rows])


@api.post("/proyek")
def buat_proyek():
    data = validasi_proyek(request.get_json(silent=True))
    new_id, _ = db().execute(
        "INSERT INTO proyek (nama, deskripsi, target_f1) VALUES (%s, %s, %s)",
        (data["nama"], data["deskripsi"], data["target_f1"]),
    )
    return _proyek_lengkap(new_id), 201


def _proyek_lengkap(proyek_id):
    rows = db().query("SELECT * FROM proyek WHERE id = %s", (proyek_id,))
    if not rows:
        return galat("Buku tidak ditemukan. Mungkin sudah dihapus, muat ulang halaman.", 404)
    runs = db().query("SELECT * FROM percobaan WHERE proyek_id = %s ORDER BY id", (proyek_id,))
    data = serialize.proyek(rows[0])
    data["percobaan"] = [serialize.percobaan(r) for r in runs]
    return jsonify(data)


@api.get("/proyek/<int:proyek_id>")
def ambil_proyek(proyek_id):
    return _proyek_lengkap(proyek_id)


@api.delete("/proyek/<int:proyek_id>")
def hapus_proyek(proyek_id):
    _, terhapus = db().execute("DELETE FROM proyek WHERE id = %s", (proyek_id,))
    if not terhapus:
        return galat("Buku tidak ditemukan. Mungkin sudah dihapus, muat ulang halaman.", 404)
    return "", 204


@api.post("/proyek/<int:proyek_id>/percobaan")
def catat_percobaan(proyek_id):
    data = validasi_percobaan(request.get_json(silent=True))
    if not db().query("SELECT id FROM proyek WHERE id = %s", (proyek_id,)):
        return galat("Buku tidak ditemukan. Mungkin sudah dihapus, muat ulang halaman.", 404)
    new_id, _ = db().execute(
        """
        INSERT INTO percobaan
            (proyek_id, nama, tahap, model, f1_macro, accuracy, invalid_count, n_data, waktu_detik, catatan)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            proyek_id,
            data["nama"],
            data["tahap"],
            data["model"],
            data["f1_macro"],
            data["accuracy"],
            data["invalid_count"],
            data["n_data"],
            data["waktu_detik"],
            data["catatan"],
        ),
    )
    row = db().query("SELECT * FROM percobaan WHERE id = %s", (new_id,))[0]
    return jsonify(serialize.percobaan(row)), 201


@api.patch("/percobaan/<int:percobaan_id>")
def ubah_catatan(percobaan_id):
    catatan = validasi_catatan(request.get_json(silent=True))
    db().execute("UPDATE percobaan SET catatan = %s WHERE id = %s", (catatan, percobaan_id))
    rows = db().query("SELECT * FROM percobaan WHERE id = %s", (percobaan_id,))
    if not rows:
        return galat("Percobaan tidak ditemukan. Mungkin sudah dihapus, muat ulang halaman.", 404)
    return jsonify(serialize.percobaan(rows[0]))


@api.delete("/percobaan/<int:percobaan_id>")
def hapus_percobaan(percobaan_id):
    _, terhapus = db().execute("DELETE FROM percobaan WHERE id = %s", (percobaan_id,))
    if not terhapus:
        return galat("Percobaan tidak ditemukan. Mungkin sudah dihapus, muat ulang halaman.", 404)
    return "", 204

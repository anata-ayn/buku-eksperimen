import os
import tempfile
import unittest

from app import create_app
from app.db import SQLiteDatabase
from app.seed import pasang_contoh


def bikin_klien(edit_key=""):
    handle, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(handle)
    database = SQLiteDatabase(path)
    database.create_schema()
    app = create_app(database, edit_key)
    app.testing = True
    return app.test_client(), database, path


PERCOBAAN = {
    "nama": "Iterasi uji",
    "tahap": "validasi",
    "model": "model-x",
    "f1_macro": "0,8123",
    "accuracy": 0.8,
    "invalid_count": 1,
    "n_data": 30,
    "waktu_detik": "12,5",
    "catatan": "catatan uji",
}


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client, self.db, self.path = bikin_klien()

    def tearDown(self):
        os.remove(self.path)

    def buat_proyek(self, **extra):
        body = {"nama": "Buku uji", "deskripsi": "desk", "target_f1": "0,7"}
        body.update(extra)
        return self.client.post("/api/proyek", json=body)

    def test_healthz_ok(self):
        r = self.client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_beranda_menyajikan_html(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"<html", r.data)

    def test_buat_dan_baca_proyek(self):
        r = self.buat_proyek()
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertEqual(data["target_f1"], 0.7)
        self.assertEqual(data["percobaan"], [])
        daftar = self.client.get("/api/proyek").get_json()
        self.assertEqual(len(daftar), 1)
        self.assertEqual(daftar[0]["jumlah_percobaan"], 0)
        self.assertIsNone(daftar[0]["f1_terbaik"])

    def test_proyek_tanpa_nama_ditolak(self):
        r = self.buat_proyek(nama="   ")
        self.assertEqual(r.status_code, 400)
        self.assertIn("wajib", r.get_json()["error"])

    def test_target_di_luar_rentang_ditolak(self):
        self.assertEqual(self.buat_proyek(target_f1=1.5).status_code, 400)

    def test_catat_percobaan_menerima_koma_desimal(self):
        pid = self.buat_proyek().get_json()["id"]
        r = self.client.post(f"/api/proyek/{pid}/percobaan", json=PERCOBAAN)
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertAlmostEqual(data["f1_macro"], 0.8123)
        self.assertAlmostEqual(data["waktu_detik"], 12.5)
        daftar = self.client.get("/api/proyek").get_json()
        self.assertEqual(daftar[0]["jumlah_percobaan"], 1)
        self.assertAlmostEqual(daftar[0]["f1_terbaik"], 0.8123)

    def test_percobaan_invalid_lebih_besar_dari_n_ditolak(self):
        pid = self.buat_proyek().get_json()["id"]
        r = self.client.post(f"/api/proyek/{pid}/percobaan", json=dict(PERCOBAAN, invalid_count=31))
        self.assertEqual(r.status_code, 400)

    def test_percobaan_f1_di_luar_rentang_ditolak(self):
        pid = self.buat_proyek().get_json()["id"]
        r = self.client.post(f"/api/proyek/{pid}/percobaan", json=dict(PERCOBAAN, f1_macro=1.2))
        self.assertEqual(r.status_code, 400)

    def test_percobaan_tahap_salah_ditolak(self):
        pid = self.buat_proyek().get_json()["id"]
        r = self.client.post(f"/api/proyek/{pid}/percobaan", json=dict(PERCOBAAN, tahap="final"))
        self.assertEqual(r.status_code, 400)

    def test_percobaan_ke_proyek_yang_tidak_ada(self):
        r = self.client.post("/api/proyek/999/percobaan", json=PERCOBAAN)
        self.assertEqual(r.status_code, 404)

    def test_ubah_catatan(self):
        pid = self.buat_proyek().get_json()["id"]
        rid = self.client.post(f"/api/proyek/{pid}/percobaan", json=PERCOBAAN).get_json()["id"]
        r = self.client.patch(f"/api/percobaan/{rid}", json={"catatan": "sudah diperbarui"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["catatan"], "sudah diperbarui")

    def test_hapus_percobaan_dan_proyek_cascade(self):
        pid = self.buat_proyek().get_json()["id"]
        rid = self.client.post(f"/api/proyek/{pid}/percobaan", json=PERCOBAAN).get_json()["id"]
        self.assertEqual(self.client.delete(f"/api/percobaan/{rid}").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/percobaan/{rid}").status_code, 404)
        self.client.post(f"/api/proyek/{pid}/percobaan", json=PERCOBAAN)
        self.assertEqual(self.client.delete(f"/api/proyek/{pid}").status_code, 204)
        self.assertEqual(self.db.query("SELECT COUNT(*) AS n FROM percobaan")[0]["n"], 0)

    def test_json_rusak_ditolak(self):
        r = self.client.post("/api/proyek", data="bukan json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_payload_terlalu_besar(self):
        r = self.client.post("/api/proyek", json={"nama": "x" * 40000})
        self.assertEqual(r.status_code, 413)

    def test_seed_modul_2a_hanya_sekali(self):
        self.assertTrue(pasang_contoh(self.db))
        self.assertFalse(pasang_contoh(self.db))
        proyek = self.client.get("/api/proyek").get_json()[0]
        self.assertEqual(proyek["jumlah_percobaan"], 9)
        self.assertAlmostEqual(proyek["f1_terbaik"], 0.8667)

    def test_data_bertahan_antar_instance_aplikasi(self):
        self.buat_proyek()
        app_baru = create_app(SQLiteDatabase(self.path))
        app_baru.testing = True
        daftar = app_baru.test_client().get("/api/proyek").get_json()
        self.assertEqual(len(daftar), 1)


class KunciTulisTest(unittest.TestCase):
    def setUp(self):
        self.client, self.db, self.path = bikin_klien(edit_key="rahasia123")

    def tearDown(self):
        os.remove(self.path)

    def test_status_melaporkan_terkunci(self):
        self.assertTrue(self.client.get("/api/status").get_json()["tulis_terkunci"])

    def test_baca_tetap_terbuka(self):
        self.assertEqual(self.client.get("/api/proyek").status_code, 200)

    def test_tulis_tanpa_kunci_ditolak(self):
        r = self.client.post("/api/proyek", json={"nama": "x"})
        self.assertEqual(r.status_code, 401)

    def test_tulis_dengan_kunci_salah_ditolak(self):
        r = self.client.post("/api/proyek", json={"nama": "x"}, headers={"X-Edit-Key": "salah"})
        self.assertEqual(r.status_code, 401)

    def test_tulis_dengan_kunci_benar(self):
        r = self.client.post("/api/proyek", json={"nama": "x"}, headers={"X-Edit-Key": "rahasia123"})
        self.assertEqual(r.status_code, 201)


if __name__ == "__main__":
    unittest.main()

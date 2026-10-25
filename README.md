# Buku Eksperimen

Catatan eksperimen model AI. Satu buku untuk satu modul atau satu model, tiap percobaan menyimpan nama, tahap uji (validasi atau test), model, F1 macro, akurasi, jumlah jawaban invalid, waktu, dan catatan. Grafik di bagian atas menunjukkan jejak F1 dari percobaan ke percobaan, lengkap dengan garis target.

Data awal diambil dari praktikum Modul 2A (klasifikasi status akademik dengan LLM), jadi grafiknya langsung terisi saat pertama dijalankan.

## Arsitektur

| Container | Isi | Port |
|-----------|-----|------|
| `app` | Flask + gunicorn, melayani API dan halaman web | 80 di host menuju 3000 di container |
| `database` | MySQL 8.4 | tidak dibuka ke luar |

- Jaringan `backend` bersifat `internal: true`, hanya `app` dan `database` yang tersambung ke sana. Database tidak punya port yang ter-publish.
- Data MySQL disimpan di volume `mysql_data`, jadi tetap ada setelah `docker compose down`.
- `database` punya healthcheck (`mysqladmin ping`). `app` baru dijalankan setelah database `healthy` (`depends_on` dengan `service_healthy`).
- Semua service memakai `restart: unless-stopped`.
- Dockerfile memakai multi-stage build: tahap `builder` memasang dependensi ke virtualenv, tahap `runtime` hanya membawa virtualenv itu dan kode aplikasi, dijalankan sebagai user non-root.

## Menjalankan dengan Docker

```bash
cp .env.example .env
# isi semua nilai di .env, minimal DB_PASSWORD, MYSQL_ROOT_PASSWORD, dan EDIT_KEY
docker compose up -d --build
docker compose ps
```

Buka `http://localhost` (atau `http://<IP_PUBLIC_VM>` di Azure VM).

Variabel di `.env`:

| Nama | Fungsi |
|------|--------|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Database dan akun yang dipakai aplikasi |
| `MYSQL_ROOT_PASSWORD` | Password root MySQL, dipakai healthcheck |
| `EDIT_KEY` | Kunci untuk menambah, mengubah, dan menghapus data. Kosongkan kalau tidak perlu, tapi di IP publik sebaiknya diisi |
| `RUN_SEED` | `true` memasang data contoh Modul 2A hanya bila database masih kosong |

Hindari karakter `$` di password karena Docker Compose menganggapnya variabel.

## Perintah yang sering dipakai

```bash
docker compose ps                  # status dan health
docker compose logs -f app         # log aplikasi
docker compose down                # hentikan, data tetap ada
docker compose down -v             # hentikan dan HAPUS data
docker compose up -d --build       # bangun ulang dan jalankan
```

## Menjalankan tanpa Docker (pengembangan)

```bash
python -m venv .venv && source .venv/bin/activate
pip install Flask
export DB_BACKEND=sqlite RUN_SEED=true
python -m app.prepare
python -m flask --app wsgi run --port 3000
python -m unittest discover -s tests -t .
```

Mode `sqlite` hanya untuk pengembangan dan pengujian. Saat dijalankan lewat Docker, aplikasi memakai MySQL.

## API

| Metode | Alamat | Fungsi |
|--------|--------|--------|
| GET | `/healthz` | Cek aplikasi dan database |
| GET | `/api/proyek` | Daftar buku beserta F1 tertinggi |
| POST | `/api/proyek` | Buat buku |
| GET, DELETE | `/api/proyek/<id>` | Baca buku dengan percobaannya, atau hapus |
| POST | `/api/proyek/<id>/percobaan` | Catat percobaan |
| PATCH, DELETE | `/api/percobaan/<id>` | Ubah catatan, atau hapus percobaan |

Permintaan POST, PATCH, dan DELETE memerlukan header `X-Edit-Key` bila `EDIT_KEY` diisi.

## Lisensi font

Font Carlito (SIL Open Font License) di `static/fonts/`, lihat `static/fonts/LICENSE.txt`.

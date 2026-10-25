MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

PROYEK = {
    "nama": "Modul 2A: status akademik dengan LLM",
    "deskripsi": (
        "Klasifikasi Aman, Waspada, dan Berisiko untuk 1.000 mahasiswa memakai LLM lewat API NVIDIA. "
        "Prompt dipilih di 30 data validasi, lalu diuji sekali di 200 data test."
    ),
    "target_f1": 0.70,
}

PERCOBAAN = [
    ("Iterasi 7: prompt aturan + few-shot anchor", "validasi", 0.6386, 0.7000, 0, 30, 289.65,
     "Prompt berisi aturan jika-maka. Waspada hanya terdeteksi 2 dari 10 (recall 0,20)."),
    ("Iterasi 8: prompt aturan + 4 contoh Berisiko", "validasi", 0.6109, 0.6333, 0, 30, 323.12,
     "Contoh tambahan tidak menolong, 5 Waspada ditebak Berisiko."),
    ("Iterasi 9: langkah eksplisit", "validasi", 0.3769, 0.4000, 1, 30, 344.81,
     "Paling buruk dari semua percobaan. Menambah langkah eksplisit justru menurunkan hasil, dan ada 1 jawaban tidak terbaca."),
    ("Iterasi 7 di data test", "test", 0.5301, 0.5800, 1, 200, 2297.23,
     "Belum lolos gerbang 0,70. Waspada: recall 0,18, F1 cuma 0,23. Pendekatan aturan jika-maka mentok di sini."),
    ("Iterasi 1: zero-shot", "validasi", 0.5924, 0.6667, 0, 30, 271.86,
     "Mulai ulang sesuai modul. 9 dari 10 data Berisiko ditebak Waspada."),
    ("Iterasi 2: few-shot, 2 contoh per kelas", "validasi", 0.7348, 0.7333, 0, 30, 365.02,
     "Contoh membantu, tapi 3 Aman dan 5 Berisiko masih jatuh ke Waspada."),
    ("Iterasi 3: few-shot + profil median kelas", "validasi", 0.6640, 0.6667, 0, 30, 369.51,
     "Turun. Median antar kelas banyak yang tumpang tindih, 6 Aman ditebak Waspada."),
    ("Iterasi 4: rubrik skor + contoh berhitung", "validasi", 0.8667, 0.8667, 0, 30, 320.42,
     "Label ternyata ditentukan skor gabungan: 30 x IPK + kehadiran + jam belajar + tugas/2 + UTS/2. Model menghitung dulu, lalu menjawab Status."),
    ("Iterasi 4 di data test", "test", 0.8329, 0.8400, 0, 200, 2496.95,
     "Lolos gerbang. Tidak ada Aman yang tertukar dengan Berisiko. Waspada tetap yang tersulit (F1 0,72)."),
]


def pasang_contoh(db):
    if db.query("SELECT COUNT(*) AS jumlah FROM proyek")[0]["jumlah"]:
        return False
    proyek_id, _ = db.execute(
        "INSERT INTO proyek (nama, deskripsi, target_f1) VALUES (%s, %s, %s)",
        (PROYEK["nama"], PROYEK["deskripsi"], PROYEK["target_f1"]),
    )
    for nama, tahap, f1, acc, invalid, n, waktu, catatan in PERCOBAAN:
        db.execute(
            """
            INSERT INTO percobaan
                (proyek_id, nama, tahap, model, f1_macro, accuracy, invalid_count, n_data, waktu_detik, catatan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (proyek_id, nama, tahap, MODEL, f1, acc, invalid, n, waktu, catatan),
        )
    return True

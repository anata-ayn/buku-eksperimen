MYSQL_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS proyek (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        nama VARCHAR(80) NOT NULL,
        deskripsi VARCHAR(400) NOT NULL DEFAULT '',
        target_f1 DECIMAL(5,4) NULL,
        dibuat_pada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS percobaan (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        proyek_id INT UNSIGNED NOT NULL,
        nama VARCHAR(120) NOT NULL,
        tahap ENUM('validasi','test') NOT NULL,
        model VARCHAR(120) NOT NULL DEFAULT '',
        f1_macro DECIMAL(5,4) NOT NULL,
        accuracy DECIMAL(5,4) NOT NULL,
        invalid_count INT UNSIGNED NOT NULL DEFAULT 0,
        n_data INT UNSIGNED NOT NULL,
        waktu_detik DECIMAL(10,2) NULL,
        catatan VARCHAR(1000) NOT NULL DEFAULT '',
        dicatat_pada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_percobaan_proyek FOREIGN KEY (proyek_id)
            REFERENCES proyek (id) ON DELETE CASCADE,
        KEY idx_percobaan_proyek (proyek_id, id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]

SQLITE_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS proyek (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        deskripsi TEXT NOT NULL DEFAULT '',
        target_f1 REAL NULL,
        dibuat_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS percobaan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyek_id INTEGER NOT NULL REFERENCES proyek (id) ON DELETE CASCADE,
        nama TEXT NOT NULL,
        tahap TEXT NOT NULL CHECK (tahap IN ('validasi','test')),
        model TEXT NOT NULL DEFAULT '',
        f1_macro REAL NOT NULL,
        accuracy REAL NOT NULL,
        invalid_count INTEGER NOT NULL DEFAULT 0,
        n_data INTEGER NOT NULL,
        waktu_detik REAL NULL,
        catatan TEXT NOT NULL DEFAULT '',
        dicatat_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

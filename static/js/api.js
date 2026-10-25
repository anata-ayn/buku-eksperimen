const KUNCI = "buku-eksperimen:kunci";

export class GalatApi extends Error {
  constructor(pesan, status) {
    super(pesan);
    this.status = status;
  }
}

export const kunci = {
  ambil() {
    try { return sessionStorage.getItem(KUNCI) || ""; } catch { return ""; }
  },
  simpan(nilai) {
    try { sessionStorage.setItem(KUNCI, nilai); } catch { /* sessionStorage bisa saja diblokir */ }
  },
};

async function panggil(metode, alamat, isi) {
  const header = { Accept: "application/json" };
  if (isi !== undefined) header["Content-Type"] = "application/json";
  const k = kunci.ambil();
  if (k) header["X-Edit-Key"] = k;

  let resp;
  try {
    resp = await fetch(alamat, { method: metode, headers: header, body: isi === undefined ? undefined : JSON.stringify(isi) });
  } catch {
    throw new GalatApi("Server tidak terjangkau. Cek koneksi internet atau pastikan container app masih berjalan.", 0);
  }
  if (resp.status === 204) return null;
  let data = null;
  try { data = await resp.json(); } catch { /* badan kosong atau bukan JSON */ }
  if (!resp.ok) throw new GalatApi((data && data.error) || `Permintaan gagal (kode ${resp.status}).`, resp.status);
  return data;
}

export const api = {
  status: () => panggil("GET", "/api/status"),
  daftarBuku: () => panggil("GET", "/api/proyek"),
  buku: (id) => panggil("GET", `/api/proyek/${id}`),
  buatBuku: (data) => panggil("POST", "/api/proyek", data),
  hapusBuku: (id) => panggil("DELETE", `/api/proyek/${id}`),
  catat: (id, data) => panggil("POST", `/api/proyek/${id}/percobaan`, data),
  ubahCatatan: (id, catatan) => panggil("PATCH", `/api/percobaan/${id}`, { catatan }),
  hapusPercobaan: (id) => panggil("DELETE", `/api/percobaan/${id}`),
};

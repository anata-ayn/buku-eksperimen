import { api, GalatApi, kunci } from "./api.js";
import { detik, skor, target as fmtTarget } from "./format.js";
import { gambarGrafik, sorotTitik } from "./chart.js";

const $ = (s, akar = document) => akar.querySelector(s);
const daftarEl = $("#daftar-buku");
const isiEl = $("#isi");
const statusEl = $("#status");
const kunciEl = $("#kunci");

const state = { daftar: [], aktif: null, detail: null, terkunci: false, sudahDianimasi: new Set() };

function h(tag, atribut = {}, ...anak) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(atribut)) {
    if (v === false || v == null) continue;
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const a of anak.flat()) if (a != null && a !== false) e.append(a);
  return e;
}

function lapor(pesan, galat = false) {
  statusEl.textContent = pesan;
  statusEl.classList.toggle("galat", galat);
}

function tanganiGalat(err, penampung) {
  if (err instanceof GalatApi && err.status === 401) {
    kunciEl.hidden = false;
    $("#isi-kunci").focus();
  }
  const pesan = err instanceof GalatApi ? err.message : "Terjadi kesalahan tak terduga. Muat ulang halaman lalu coba lagi.";
  if (penampung) penampung.textContent = pesan;
  else lapor(pesan, true);
}

function ambilForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function rakBuku() {
  daftarEl.replaceChildren();
  if (!state.daftar.length) {
    daftarEl.append(h("li", { class: "kosong" }, "Belum ada buku."));
    return;
  }
  for (const b of state.daftar) {
    daftarEl.append(
      h("li", {},
        h("a", { href: `#/buku/${b.id}`, "aria-current": b.id === state.aktif ? "page" : false },
          h("span", {}, b.nama),
          h("span", { class: "skor angka", title: "F1 macro tertinggi" }, b.f1_terbaik == null ? "kosong" : skor(b.f1_terbaik)))));
  }
}

async function muatDaftar() {
  state.daftar = await api.daftarBuku();
  rakBuku();
}

function idDariHash() {
  const m = location.hash.match(/^#\/buku\/(\d+)$/);
  return m ? Number(m[1]) : null;
}

async function buka() {
  let id = idDariHash();
  if (id === null || !state.daftar.some((b) => b.id === id)) id = state.daftar.length ? state.daftar[0].id : null;
  state.aktif = id;
  rakBuku();
  if (id === null) {
    state.detail = null;
    isiEl.replaceChildren(
      h("div", { class: "kosong-halaman" },
        h("h1", {}, "Belum ada buku eksperimen."),
        h("p", {}, "Buat satu di kolom Buat buku baru. Satu buku cocok untuk satu modul atau satu model yang sedang kamu uji, nanti tiap percobaan tercatat lengkap dengan skornya.")));
    return;
  }
  try {
    state.detail = await api.buku(id);
  } catch (err) {
    isiEl.replaceChildren(h("p", { class: "galat" }, err.message));
    return;
  }
  renderBuku();
}

function renderBuku() {
  const d = state.detail;
  const kepala = h("header", { class: "kepala" },
    h("h1", {}, d.nama),
    d.deskripsi ? h("p", { class: "deskripsi" }, d.deskripsi) : null,
    d.target_f1 != null
      ? h("p", { class: "target" }, "Target F1 macro ", h("b", { class: "angka" }, fmtTarget(d.target_f1)), ", ditandai garis merah di grafik.")
      : null,
    tombolHapusBuku());

  const wadahGrafik = h("div", { class: "grafik", id: "grafik" });
  const bagianGrafik = h("section", { "aria-labelledby": "j-grafik" },
    h("h2", { id: "j-grafik" }, "Jejak F1 macro"),
    h("p", { class: "sub" }, "Titik disusun menurut urutan percobaan. Klik titik untuk melompat ke catatannya."),
    wadahGrafik,
    legenda());

  const bagianLog = h("section", { "aria-labelledby": "j-log" },
    h("h2", { id: "j-log" }, "Catatan percobaan"),
    h("p", { class: "sub" }, d.percobaan.length ? `${d.percobaan.length} percobaan, dari yang pertama sampai yang terbaru.` : "Belum ada percobaan."),
    h("ol", { class: "log", id: "log" }, d.percobaan.map((p, i) => baris(p, i))));

  isiEl.replaceChildren(kepala, bagianGrafik, bagianLog, bagianForm());
  const animasi = !state.sudahDianimasi.has(d.id);
  state.sudahDianimasi.add(d.id);
  const gambar = (ani) => gambarGrafik(wadahGrafik, d.percobaan, d.target_f1, sorotBaris, ani);
  gambar(animasi);
  let lebarTerakhir = wadahGrafik.clientWidth;
  let tunggu = 0;
  new ResizeObserver(() => {
    if (Math.abs(wadahGrafik.clientWidth - lebarTerakhir) < 2) return;
    lebarTerakhir = wadahGrafik.clientWidth;
    cancelAnimationFrame(tunggu);
    tunggu = requestAnimationFrame(() => gambar(false));
  }).observe(wadahGrafik);
}

function legenda() {
  const ikon = (isi) => {
    const wadah = h("span", { "aria-hidden": "true" });
    wadah.innerHTML = isi;
    return wadah.firstChild;
  };
  const svg = (x) => `<svg viewBox="0 0 22 14" aria-hidden="true">${x}</svg>`;
  return h("p", { class: "legenda" },
    h("span", {}, ikon(svg('<circle cx="11" cy="7" r="5" fill="#1b3fa0"/>')), "percobaan di data validasi"),
    h("span", {}, ikon(svg('<rect x="5.5" y="1.5" width="11" height="11" fill="#f7faf6" stroke="#1b3fa0" stroke-width="2.25"/>')), "percobaan di data test"),
    h("span", {}, ikon(svg('<line x1="0" y1="7" x2="22" y2="7" stroke="#b82a2a" stroke-width="1.6" stroke-dasharray="6 4"/>')), "target"),
    h("span", {}, ikon(svg('<ellipse cx="11" cy="7" rx="9" ry="5.5" fill="none" stroke="#b82a2a" stroke-width="1.7" transform="rotate(-10 11 7)"/>')), "F1 tertinggi"));
}

function sorotBaris(id) {
  const target = document.getElementById(`p-${id}`);
  if (!target) return;
  document.querySelectorAll(".baris.sorot").forEach((e) => e.classList.remove("sorot"));
  target.classList.add("sorot");
  target.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  setTimeout(() => target.classList.remove("sorot"), 2200);
}

function vonis(p, targetF1) {
  if (p.tahap !== "test" || targetF1 == null) return null;
  return p.f1_macro >= targetF1
    ? h("span", { class: "vonis lolos" }, "lolos target")
    : h("span", { class: "vonis belum" }, `di bawah target ${fmtTarget(targetF1)}`);
}

function baris(p, i) {
  const targetF1 = state.detail.target_f1;
  const li = h("li", { class: "baris", id: `p-${p.id}`, onmouseenter: () => sorotTitik($("#grafik"), p.id, true), onmouseleave: () => sorotTitik($("#grafik"), p.id, false) },
    h("span", { class: "no" }, String(i + 1)),
    h("h3", {}, p.nama),
    h("p", { class: "f1" }, h("span", { class: "angka" }, skor(p.f1_macro)), vonis(p, targetF1)),
    h("p", { class: "meta angka" },
      h("span", { class: "tahap" }, p.tahap === "test" ? "data test" : "data validasi"),
      p.model ? h("span", {}, p.model) : null,
      h("span", {}, `akurasi ${skor(p.accuracy)}`),
      h("span", {}, `${p.n_data} data`),
      h("span", {}, `invalid ${p.invalid_count}`),
      p.waktu_detik != null ? h("span", {}, detik(p.waktu_detik)) : null));
  const slotCatatan = h("div", { class: "slot-catatan" });
  li.append(slotCatatan);
  tampilCatatan(slotCatatan, p);
  li.append(h("div", { class: "aksi" }, tombolUbah(slotCatatan, p), tombolHapusPercobaan(p)));
  return li;
}

function tampilCatatan(slot, p) {
  slot.replaceChildren(h("p", { class: p.catatan ? "catatan" : "catatan kosong" }, p.catatan || "Belum ada catatan."));
}

function tombolUbah(slot, p) {
  const tombol = h("button", { type: "button", class: "tautan", onclick: () => {
    const area = h("textarea", { rows: 3, maxlength: 1000, "aria-label": `Catatan untuk ${p.nama}` }, p.catatan);
    const galat = h("p", { class: "galat", role: "alert" });
    const simpan = h("button", { type: "button", class: "tombol", onclick: async () => {
      simpan.disabled = true;
      try {
        const baru = await api.ubahCatatan(p.id, area.value);
        p.catatan = baru.catatan;
        tampilCatatan(slot, p);
        tombol.hidden = false;
        lapor("Catatan tersimpan.");
      } catch (err) {
        tanganiGalat(err, galat);
        simpan.disabled = false;
      }
    } }, "Simpan catatan");
    const batal = h("button", { type: "button", class: "tautan", onclick: () => { tampilCatatan(slot, p); tombol.hidden = false; } }, "Batal");
    slot.replaceChildren(h("div", { class: "edit" }, area, h("div", { class: "tombol-baris" }, simpan, batal), galat));
    tombol.hidden = true;
    area.focus();
  } }, "Ubah catatan");
  return tombol;
}

function konfirmasiHapus(label, tanya, aksi) {
  const tombol = h("button", { type: "button", class: "tautan bahaya", onclick: () => {
    const ya = h("button", { type: "button", class: "tautan bahaya", onclick: async () => {
      ya.disabled = true;
      try { await aksi(); } catch (err) { tanganiGalat(err); wadah.replaceChildren(tombol); }
    } }, "Ya, hapus");
    const batal = h("button", { type: "button", class: "tautan", onclick: () => { wadah.replaceChildren(tombol); tombol.focus(); } }, "Batal");
    wadah.replaceChildren(h("span", {}, `${tanya} `), ya, " ", batal);
    batal.focus();
  } }, label);
  const wadah = h("span", {}, tombol);
  return wadah;
}

function tombolHapusPercobaan(p) {
  return konfirmasiHapus("Hapus", "Hapus percobaan ini?", async () => {
    await api.hapusPercobaan(p.id);
    lapor("Percobaan dihapus.");
    await muatDaftar();
    await buka();
  });
}

function tombolHapusBuku() {
  const d = state.detail;
  return h("div", { class: "hapus-buku" },
    konfirmasiHapus("Hapus buku ini", `Hapus buku beserta ${d.percobaan.length} percobaannya?`, async () => {
      await api.hapusBuku(d.id);
      lapor(`Buku "${d.nama}" dihapus.`);
      location.hash = "";
      await muatDaftar();
      await buka();
    }));
}

function bagianForm() {
  const terakhir = state.detail.percobaan.at(-1);
  const isian = (label, nama, opsi = {}) =>
    h("label", { class: opsi.kelas }, label, h("input", { name: nama, autocomplete: "off", ...opsi.atribut }));
  const form = h("form", { class: "form-percobaan", novalidate: true, onsubmit: async (e) => {
    e.preventDefault();
    const tombol = $("button[type=submit]", form);
    const galat = $("[data-galat]", form);
    galat.textContent = "";
    tombol.disabled = true;
    try {
      const data = ambilForm(form);
      const baru = await api.catat(state.detail.id, data);
      lapor(`Tercatat sebagai percobaan ke-${state.detail.percobaan.length + 1}: ${baru.nama}.`);
      await muatDaftar();
      await buka();
      document.getElementById(`p-${baru.id}`)?.scrollIntoView({ block: "center" });
    } catch (err) {
      tanganiGalat(err, galat);
      tombol.disabled = false;
    }
  } },
    isian("Nama percobaan", "nama", { kelas: "l-nama", atribut: { maxlength: 120, required: true, placeholder: "Iterasi 5: contoh lebih banyak" } }),
    h("label", { class: "l-tahap" }, "Diuji di",
      h("select", { name: "tahap" }, h("option", { value: "validasi" }, "validasi"), h("option", { value: "test" }, "test"))),
    isian("Model", "model", { kelas: "l-model", atribut: { maxlength: 120, value: terakhir ? terakhir.model : "", placeholder: "nama model" } }),
    isian("F1 macro", "f1_macro", { kelas: "l-angka", atribut: { inputmode: "decimal", required: true, placeholder: "0,8329" } }),
    isian("Akurasi", "accuracy", { kelas: "l-angka", atribut: { inputmode: "decimal", required: true, placeholder: "0,8400" } }),
    isian("Jumlah data", "n_data", { kelas: "l-kecil", atribut: { inputmode: "numeric", required: true, placeholder: "200" } }),
    isian("Invalid", "invalid_count", { kelas: "l-kecil", atribut: { inputmode: "numeric", value: "0", required: true } }),
    isian("Waktu (detik)", "waktu_detik", { kelas: "l-kecil", atribut: { inputmode: "decimal", placeholder: "boleh kosong" } }),
    h("label", { class: "l-catatan" }, "Catatan",
      h("textarea", { name: "catatan", rows: 3, maxlength: 1000, placeholder: "Apa yang diubah dan apa yang terlihat di hasilnya." })),
    h("div", { class: "kirim" },
      h("button", { type: "submit", class: "tombol" }, "Catat percobaan"),
      h("p", { class: "galat", "data-galat": true, role: "alert" })));
  return h("section", { "aria-labelledby": "j-form" },
    h("h2", { id: "j-form" }, "Tulis percobaan berikutnya"),
    h("p", { class: "sub" }, "Angka desimal boleh ditulis dengan koma. \"Invalid\" adalah jumlah jawaban model yang tidak terbaca sebagai label."),
    form);
}

$("#form-buku").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const tombol = $("button[type=submit]", form);
  const galat = $("[data-galat]", form);
  galat.textContent = "";
  tombol.disabled = true;
  try {
    const baru = await api.buatBuku(ambilForm(form));
    form.reset();
    $("#buku-baru").open = false;
    await muatDaftar();
    location.hash = `#/buku/${baru.id}`;
    lapor(`Buku "${baru.nama}" dibuat.`);
  } catch (err) {
    tanganiGalat(err, galat);
  } finally {
    tombol.disabled = false;
  }
});

$("#form-kunci").addEventListener("submit", (e) => {
  e.preventDefault();
  kunci.simpan($("#isi-kunci").value);
  kunciEl.hidden = true;
  lapor("Kunci tersimpan untuk tab ini. Ulangi aksi yang tadi gagal.");
});

window.addEventListener("hashchange", buka);

(async function mulai() {
  try {
    const st = await api.status();
    state.terkunci = st.tulis_terkunci;
    if (state.terkunci && !kunci.ambil()) kunciEl.hidden = false;
    await muatDaftar();
    await buka();
  } catch (err) {
    isiEl.replaceChildren(h("p", { class: "galat" }, `${err.message} Kalau ini di VM, cek docker compose ps: container database harus berstatus healthy.`));
  }
})();

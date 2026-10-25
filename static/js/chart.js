import { skor, target as fmtTarget, sumbu } from "./format.js";

const NS = "http://www.w3.org/2000/svg";
const KOTAK = 14;
const BAGI = 20;

function el(nama, atribut = {}, anak = []) {
  const e = document.createElementNS(NS, nama);
  for (const [k, v] of Object.entries(atribut)) e.setAttribute(k, v);
  for (const a of anak) e.append(a);
  return e;
}

function teks(isi, atribut) {
  const t = el("text", atribut);
  t.textContent = isi;
  return t;
}

export function gambarGrafik(wadah, percobaan, targetF1, saatPilih, animasi = false) {
  wadah.replaceChildren();
  const lebar = Math.max(wadah.clientWidth, 280);
  const lebarRuang = lebar;
  const targetDiLuar = lebarRuang >= 640;
  const kiri = 46, kanan = targetDiLuar ? 84 : 20, atas = 28, bawah = 40;
  const tinggiPlot = KOTAK * BAGI;
  const tinggi = atas + tinggiPlot + bawah;
  const lebarPlot = lebar - kiri - kanan;
  const svg = el("svg", { viewBox: `0 0 ${lebar} ${tinggi}`, role: "img", "aria-label": ringkasAria(percobaan, targetF1) });

  const y = (nilai) => atas + tinggiPlot * (1 - nilai);
  const inset = Math.min(28, lebarPlot / 6);
  const x = (i, n) => (n === 1 ? kiri + lebarPlot / 2 : kiri + inset + (i * (lebarPlot - 2 * inset)) / (n - 1));

  for (let i = 0; i <= BAGI; i++) {
    const besar = i % 5 === 0;
    svg.append(el("line", { x1: kiri, x2: kiri + lebarPlot, y1: y(i / BAGI), y2: y(i / BAGI), stroke: besar ? "#bcd6c2" : "#dbe8dd", "stroke-width": 1 }));
    if (besar) svg.append(teks(sumbu(i / BAGI), { x: kiri - 8, y: y(i / BAGI) + 4.5, "text-anchor": "end", class: "g-label" }));
  }
  for (let px = 0; px <= lebarPlot; px += KOTAK) {
    const besar = (px / KOTAK) % 5 === 0;
    svg.append(el("line", { x1: kiri + px, x2: kiri + px, y1: atas, y2: atas + tinggiPlot, stroke: besar ? "#bcd6c2" : "#dbe8dd", "stroke-width": 1 }));
  }
  svg.append(el("line", { x1: kiri, x2: kiri, y1: atas, y2: atas + tinggiPlot, class: "g-sumbu" }));
  svg.append(el("line", { x1: kiri, x2: kiri + lebarPlot, y1: y(0), y2: y(0), class: "g-sumbu" }));
  svg.append(teks("percobaan ke", { x: kiri + lebarPlot, y: tinggi - 4, "text-anchor": "end", class: "g-label" }));

  if (targetF1 != null) {
    svg.append(el("line", { x1: kiri, x2: kiri + lebarPlot, y1: y(targetF1), y2: y(targetF1), class: "g-target" }));
    svg.append(
      targetDiLuar
        ? teks(`target ${fmtTarget(targetF1)}`, { x: kiri + lebarPlot + 8, y: y(targetF1) + 4.5, class: "g-target-label" })
        : teks(`target ${fmtTarget(targetF1)}`, { x: kiri + 6, y: y(targetF1) - 7, class: "g-target-label" })
    );
  }

  const n = percobaan.length;
  if (n === 0) {
    svg.append(teks("Belum ada titik. Tulis percobaan pertama di bawah, jejaknya muncul di sini.", { x: kiri + lebarPlot / 2, y: atas + tinggiPlot / 2, "text-anchor": "middle", class: "g-kosong" }));
    wadah.append(svg);
    return;
  }

  const titik = percobaan.map((p, i) => ({ p, i, cx: x(i, n), cy: y(p.f1_macro) }));
  const terbaik = titik.reduce((a, b) => (b.p.f1_macro > a.p.f1_macro ? b : a));

  if (n > 1) {
    const jalur = el("polyline", { points: titik.map((t) => `${t.cx},${t.cy}`).join(" "), class: "g-jejak" });
    svg.append(jalur);
    const panjang = titik.slice(1).reduce((s, t, k) => s + Math.hypot(t.cx - titik[k].cx, t.cy - titik[k].cy), 0);
    if (animasi && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      jalur.style.setProperty("--panjang", `${Math.ceil(panjang) + 4}`);
      jalur.classList.add("menggambar");
    }
  }

  svg.append(el("ellipse", { cx: terbaik.cx, cy: terbaik.cy, rx: 15, ry: 12, transform: `rotate(-10 ${terbaik.cx} ${terbaik.cy})`, class: "g-lingkar" }));

  const tampilkanSemua = n <= 12 && lebarPlot / n >= 44;
  for (const t of titik) {
    const { p, i, cx, cy } = t;
    const prev = titik[i - 1], next = titik[i + 1];
    const lembah = (prev && prev.cy < cy) || (next && next.cy < cy);
    const puncak = (!prev || prev.cy >= cy) && (!next || next.cy >= cy);
    const bawahTitik = lembah && !puncak;
    const g = el("g", {
      class: `g-titik ${p.tahap === "test" ? "uji" : ""}`,
      tabindex: 0,
      role: "button",
      "data-id": p.id,
      "aria-label": `Percobaan ke-${i + 1}, ${p.nama}, tahap ${p.tahap}, F1 macro ${skor(p.f1_macro)}`,
    });
    g.append(el("title", {}, [document.createTextNode(`${p.nama}: F1 ${skor(p.f1_macro)}`)]));
    g.append(el("circle", { cx, cy, r: 13, class: "cincin" }));
    g.append(
      p.tahap === "test"
        ? el("rect", { x: cx - 5.5, y: cy - 5.5, width: 11, height: 11, class: "bentuk" })
        : el("circle", { cx, cy, r: 5, class: "bentuk" })
    );
    if (tampilkanSemua || t === terbaik || i === n - 1) {
      g.append(teks(skor(p.f1_macro), { x: cx, y: bawahTitik ? cy + 25 : cy - 15, "text-anchor": "middle", class: "g-nilai" }));
    }
    g.addEventListener("click", () => saatPilih(p.id));
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); saatPilih(p.id); }
    });
    svg.append(g);
    if (n <= 24 || i % Math.ceil(n / 24) === 0) {
      svg.append(teks(String(i + 1), { x: cx, y: y(0) + 20, "text-anchor": "middle", class: "g-label" }));
    }
  }
  wadah.append(svg);
}

function ringkasAria(percobaan, targetF1) {
  if (!percobaan.length) return "Grafik F1 macro kosong, belum ada percobaan.";
  const terbaik = Math.max(...percobaan.map((p) => p.f1_macro));
  const t = targetF1 != null ? ` Target ${fmtTarget(targetF1)}.` : "";
  return `Grafik F1 macro dari ${percobaan.length} percobaan, tertinggi ${skor(terbaik)}.${t}`;
}

export function sorotTitik(wadah, id, hidup) {
  const g = wadah.querySelector(`.g-titik[data-id="${id}"]`);
  if (g) g.classList.toggle("aktif", hidup);
}

const nf = (min, max) => new Intl.NumberFormat("id-ID", { minimumFractionDigits: min, maximumFractionDigits: max });
const f1 = nf(4, 4);
const dua = nf(2, 2);
const bebas = nf(0, 2);

export const skor = (n) => f1.format(n);
export const target = (n) => dua.format(n);
export const detik = (n) => `${bebas.format(n)} dtk`;
export const sumbu = (n) => nf(0, 2).format(n);

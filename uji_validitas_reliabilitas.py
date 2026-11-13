"""
Uji Validitas Butir dan Reliabilitas (Cronbach's Alpha) per dimensi.

Cara pakai:
1. Isi bagian KONFIGURASI (nama file data dan kelas yang dipakai).
2. Jalankan: python uji_validitas_reliabilitas.py
3. Hasil tersimpan di folder output/.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# ===================== KONFIGURASI =====================
FILE_DATA = Path("data/respons_gabungan.xlsx")  # hasil ekspor Google Forms (.xlsx atau .csv)
KELAS = "3 TI A"        # hanya responden dari kelas ini yang diuji
OUTPUT_DIR = Path("output")
ALPHA = 0.05            # taraf signifikansi dua sisi
RELIABEL_MIN = 0.70     # batas minimal Cronbach's alpha dianggap reliabel
LABEL_SKALA = {1: "STS", 2: "TS", 3: "N", 4: "S", 5: "SS"}  # skala Likert 1-5
# Jawaban teks dari formulir -> angka skala
MAP_JAWABAN = {
    "Sangat Tidak Setuju (STS)": 1,
    "Tidak Setuju (TS)": 2,
    "Netral (N)": 3,
    "Setuju (S)": 4,
    "Sangat Setuju (SS)": 5,
}
# =======================================================


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        sys.exit(f"File data tidak ditemukan: {path}")
    return pd.read_excel(path) if path.suffix.lower() == ".xlsx" else pd.read_csv(path)


def siapkan_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Mengubah ekspor Google Forms menjadi tabel angka dengan kolom berkode (mis. AI1, PS1).
    Mengembalikan data butir dan dictionary: nama dimensi -> daftar kode butir.
    """
    df = raw[raw["Kelas"].astype(str).str.strip() == KELAS].copy()
    item_cols = [c for c in df.columns if str(c).strip() not in ("Cap waktu", "Kelas")]

    kode_map, dimensi = {}, {}
    for col in item_cols:
        teks = str(col)
        # Format header: "<nama dimensi> [<KODE>. <pernyataan>]"
        kode = teks.split("[", 1)[1].split(".", 1)[0].strip()
        nama_dim = teks.split("[", 1)[0].strip()
        kode_map[col] = kode
        dimensi.setdefault(nama_dim, []).append(kode)

    data = df[item_cols].rename(columns=kode_map)
    data = data.apply(lambda s: s.map(lambda v: MAP_JAWABAN.get(str(v).strip(), np.nan)))
    return data, dimensi


def r_tabel(n: int, alpha: float = ALPHA) -> float:
    """Nilai r-tabel dihitung dari distribusi t dengan df = n - 2."""
    df = n - 2
    t = stats.t.ppf(1 - alpha / 2, df)
    return t / np.sqrt(t**2 + df)


def safe_pearson(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    if x.std(ddof=1) == 0 or y.std(ddof=1) == 0:
        return np.nan, np.nan
    r, p = stats.pearsonr(x, y)
    return r, p


def cronbach_alpha(data: pd.DataFrame) -> float:
    k = data.shape[1]
    if k < 2:
        return np.nan
    sum_var_item = data.var(axis=0, ddof=1).sum()
    var_total = data.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - sum_var_item / var_total)


def interpretasi_alpha(a: float) -> str:
    if np.isnan(a):
        return "tidak dapat dihitung (butir kurang dari 2)"
    if a >= 0.90:
        return "sangat baik"
    if a >= 0.80:
        return "baik"
    if a >= RELIABEL_MIN:
        return "reliabel"
    return "tidak reliabel"


def keputusan_butir(valid: bool, alpha_del: float, alpha_dim: float) -> str:
    if np.isnan(alpha_del):
        return "Pertahankan" if valid else "Buang/revisi, uji ulang"
    if valid and alpha_del <= alpha_dim:
        return "Pertahankan"
    if valid:
        return "Tinjau isi butir"
    if alpha_del > alpha_dim:
        return "Buang/revisi, uji ulang"
    return "Tinjau ulang sebelum dibuang"


def analisis_dimensi(data: pd.DataFrame, r_tab: float) -> tuple[pd.DataFrame, dict]:
    total = data.sum(axis=1)
    alpha_dim = cronbach_alpha(data)

    rows = []
    for col in data.columns:
        r_hit, p = safe_pearson(data[col], total)                  # terhadap total dimensi
        corr_r, _ = safe_pearson(data[col], total - data[col])     # corrected item-total
        alpha_del = cronbach_alpha(data.drop(columns=col))         # alpha jika butir dihapus
        valid = bool(r_hit > r_tab) if not np.isnan(r_hit) else False
        rows.append({
            "Butir": col,
            "r_hitung": round(r_hit, 4),
            "p_value": round(p, 4),
            "Corrected r": round(corr_r, 4),
            "Alpha jika dihapus": round(alpha_del, 4) if not np.isnan(alpha_del) else "-",
            "Keterangan": "Valid" if valid else "Tidak valid",
            "Keputusan": keputusan_butir(valid, alpha_del, alpha_dim),
        })

    info = {
        "butir": data.shape[1],
        "alpha": alpha_dim,
        "kategori": interpretasi_alpha(alpha_dim),
        "rata_rata": total.mean(),
        "std": total.std(ddof=1),
        "skewness": stats.skew(total, bias=False),
        "kurtosis": stats.kurtosis(total, bias=False),
        "valid": sum(r["Keterangan"] == "Valid" for r in rows),
    }
    return pd.DataFrame(rows), info


def plot_komposisi(nama: str, data: pd.DataFrame, path: Path) -> None:
    persen = {}
    for col in data.columns:
        cnt = data[col].value_counts().reindex(range(1, 6), fill_value=0)
        persen[col] = cnt / cnt.sum() * 100
    tab = pd.DataFrame(persen).T

    fig, ax = plt.subplots(figsize=(8, 0.5 * len(data.columns) + 1.8))
    left = np.zeros(len(tab))
    for v in range(1, 6):
        ax.barh(tab.index, tab[v], left=left, label=LABEL_SKALA[v])
        left += tab[v].values
    ax.invert_yaxis()
    ax.set_xlabel("Persentase responden (%)")
    ax.set_title(f"Komposisi jawaban - {nama}")
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    raw = load_data(FILE_DATA)
    data, DIMENSI = siapkan_data(raw)
    n_awal = len(data)
    data = data.dropna()
    n = len(data)
    print(f"Kelas {KELAS}: {n_awal} responden, {n} dipakai (baris dengan data kosong dikeluarkan)")
    print("Dimensi terdeteksi:")
    for nama, kolom in DIMENSI.items():
        print(f"  {nama}: {', '.join(kolom)}")
    r_tab = r_tabel(n)
    print(f"r-tabel (alpha={ALPHA}, df={n - 2}) = {r_tab:.4f}\n")

    OUTPUT_DIR.mkdir(exist_ok=True)
    ringkasan = []

    for nama, kolom in DIMENSI.items():
        sub = data[kolom]
        tabel, info = analisis_dimensi(sub, r_tab)
        slug = "".join(c if c.isalnum() else "_" for c in nama.lower())

        tabel.to_csv(OUTPUT_DIR / f"{slug}_validitas.csv", index=False)
        plot_komposisi(nama, sub, OUTPUT_DIR / f"{slug}_komposisi.png")

        print(f"=== {nama} ===")
        print(tabel.to_string(index=False))
        print(f"Cronbach's Alpha = {info['alpha']:.4f} ({info['kategori']})")
        print(f"Skor total: rata-rata {info['rata_rata']:.2f}, std {info['std']:.3f}, "
              f"skewness {info['skewness']:.3f}, kurtosis {info['kurtosis']:.3f}\n")

        ringkasan.append({
            "Dimensi": nama,
            "Butir": info["butir"],
            "Valid": info["valid"],
            "Tidak valid": info["butir"] - info["valid"],
            "Alpha": round(info["alpha"], 4),
            "Kategori": info["kategori"],
            "Rata-rata skor total": round(info["rata_rata"], 2),
            "Std skor total": round(info["std"], 3),
            "Skewness": round(info["skewness"], 3),
            "Kurtosis": round(info["kurtosis"], 3),
        })

    ringkasan_df = pd.DataFrame(ringkasan)
    ringkasan_df.to_csv(OUTPUT_DIR / "ringkasan_dimensi.csv", index=False)
    print("=== RINGKASAN ===")
    print(ringkasan_df.to_string(index=False))

    with open(OUTPUT_DIR / "ringkasan.txt", "w", encoding="utf-8") as f:
        f.write(f"Responden dipakai: {n} dari {n_awal}\n")
        f.write(f"r-tabel (alpha={ALPHA}, df={n - 2}) = {r_tab:.4f}\n\n")
        f.write(ringkasan_df.to_string(index=False))
    print(f"\nHasil tersimpan di folder {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

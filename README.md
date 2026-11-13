# Uji Validitas dan Reliabilitas Kuesioner

Tugas Probabilitas dan Statistika, Program Studi Teknik Informatika, Politeknik Caltex Riau.

Program ini menguji validitas butir dan reliabilitas (Cronbach's Alpha) untuk setiap dimensi kuesioner, berdasarkan data kelas 3 TI A.

## Isi repo

| Path | Keterangan |
|------|------------|
| `uji_validitas_reliabilitas.py` | Program utama: uji validitas, uji reliabilitas, dan grafik komposisi jawaban |
| `requirements.txt` | Daftar library Python yang dibutuhkan |
| `data/` | File data kuesioner hasil ekspor spreadsheet |
| `output/` | Hasil pengujian (CSV, TXT, dan PNG) |

## Metode

- **Validitas butir:** korelasi Pearson antara skor butir dan skor total dimensi (r-hitung). Butir dinyatakan valid jika r-hitung > r-tabel, dengan r-tabel dihitung dari distribusi t untuk α = 0,05 dua sisi dan df = n − 2. Corrected item-total correlation juga dihitung sebagai pembanding.
- **Reliabilitas:** Cronbach's Alpha per dimensi, beserta nilai alpha jika butir dihapus. Alpha ≥ 0,70 dianggap reliabel.

## Cara menjalankan

```bash
pip install -r requirements.txt
python uji_validitas_reliabilitas.py
```

Program membaca file di folder `data/`. Dimensi dan kode butir dibaca otomatis dari header kolom formulir, dan hanya responden dengan kelas `3 TI A` yang diuji. Jika nama file berbeda, ubah `FILE_DATA` di bagian `KONFIGURASI`.

## Output

- `output/<dimensi>_validitas.csv`: tabel r-hitung, corrected r, alpha jika dihapus, dan keputusan per butir.
- `output/<dimensi>_komposisi.png`: komposisi jawaban per butir.
- `output/ringkasan_dimensi.csv` dan `output/ringkasan.txt`: ringkasan validitas dan reliabilitas seluruh dimensi.

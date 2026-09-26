# Keuangan Privat Per Cabang

Gunakan pola ini untuk keuangan franchise yang hanya boleh dilihat Owner Mitra.

## Urutan implementasi

1. Tambahkan tabel shift/ledger dengan `branch_id`, user pembuka/penutup, status, timestamp, nominal decimal, dan foreign key restriktif.
2. Tambahkan service untuk membuka shift, mencatat kas, menutup shift, dan laporan; controller hanya meneruskan request.
3. Tolak Full Owner dan role non-pelapor di middleware/controller **dan** service karena direct service calls atau route drift dapat melewati satu lapisan.
4. Periksa membership cabang sebelum setiap query atau mutasi; jangan mempercayai `branch_id` dari form.
5. Gunakan satu shift aktif per cabang dengan lock; semua POS dan kas manual harus terhubung ke shift terbuka.
6. Saat tutup, hitung server-side: `saldo sistem = saldo awal + income - expense`, lalu `selisih = saldo fisik - saldo sistem`.
7. Bedakan saldo kas dari laba/rugi; laporan laba harus memasukkan HPP dan aturan periode yang jelas.
8. Tambahkan test untuk akses Full Owner, akses karyawan ke laporan, cabang lain, shift duplikat, transaksi tanpa shift, penutupan dua kali, dan variance.

## Hak akses baseline

| Area | Full Owner | Owner Mitra | Karyawan Mitra |
|---|---:|---:|---:|
| Omzet dan laporan | Tolak | Izinkan cabang sendiri | Tolak |
| Buka/tutup shift | Tolak | Izinkan cabang sendiri | Sesuai permission |
| Kas masuk/keluar | Tolak | Izinkan cabang sendiri | Sesuai permission |
| POS | Sesuai domain stok, bukan finansial | Izinkan | Izinkan sesuai permission |

Jangan menampilkan tautan sebagai satu-satunya pengaman. Route, service, dan query harus konsisten dengan matriks ini.

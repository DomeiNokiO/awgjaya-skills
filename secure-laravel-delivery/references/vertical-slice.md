# Implementasi Vertical Slice Laravel Multi-Tenant

Gunakan urutan ini untuk setiap modul transaksi agar fitur dapat dirawat dan tidak berhenti sebagai scaffold.

## Urutan kerja

1. Tulis migration dengan `branch_id`, foreign key, index, status enum/string yang tervalidasi, decimal untuk uang/kuantitas, dan aturan delete yang mencegah data historis hilang.
2. Tambahkan model, relasi, cast, dan factory/seed data seperlunya.
3. Tulis Form Request untuk validasi bentuk input; jangan menaruh aturan bisnis penting hanya di Blade atau JavaScript.
4. Tulis policy/middleware atau service guard yang memeriksa membership user terhadap `branch_id` sebelum query maupun mutasi.
5. Tulis service domain yang menghitung ulang nilai dari database, membungkus perubahan lintas tabel dalam `DB::transaction`, dan memakai `lockForUpdate` pada saldo yang bisa diperebutkan.
6. Catat hasil mutasi ke tabel audit/movement dengan user, cabang, alasan, referensi, dan saldo setelah perubahan.
7. Tambahkan controller tipis, route dengan middleware, view yang mendukung CSRF, lalu eager-load relasi yang ditampilkan untuk menghindari N+1.
8. Tambahkan test untuk alur sukses, tenant lain ditolak, saldo tidak cukup ditolak tanpa partial write, dan role yang dilarang ditolak.
9. Tambahkan dokumentasi alur bisnis, matriks hak akses, status transition, dan instruksi update/deploy.
10. Jalankan `php artisan test`, `php artisan pint --test`, dan `php artisan route:list` jika toolchain tersedia; jika tidak, jalankan pemeriksaan statis dan tandai runtime test sebagai belum dijalankan.

## Aturan POS dan stok

- Jangan menerima harga, subtotal, total, atau saldo dari browser sebagai sumber kebenaran.
- Ambil harga produk dan resep dari database dalam transaksi.
- Kunci seluruh baris stok yang akan dikurangi sebelum memeriksa saldo.
- Simpan penjualan, item, pengurangan stok, mutasi stok, dan kas masuk dalam transaksi yang sama.
- Lempar `ValidationException` untuk kegagalan bisnis sehingga form mendapat error tanpa menulis sebagian data.
- Gunakan receipt/reference unik yang dibuat server, bukan nomor dari klien.

## Aturan dokumentasi dan rilis

- README harus menjelaskan fitur yang benar-benar ada dan memisahkan roadmap dari fitur selesai.
- Dokumentasi operasional harus memuat install, update setelah `git pull`, backup, pemulihan, TLS, dan batasan verifikasi.
- Sebelum push, pastikan file secret dan metadata Git cadangan tidak ikut ter-stage.
- Setelah push, baca kembali commit remote dan status repository; jangan menyimpulkan berhasil hanya dari output lokal.

# SolutionCorp Backend - Sistem Manajemen Bisnis ERP & Marketplace API

Proyek backend untuk sistem manajemen bisnis dan e-commerce terintegrasi **PT Solution Corp Indonesia**. Sistem ini dibangun menggunakan **Django REST Framework (DRF)** dengan arsitektur *decoupled full-stack* untuk melayani kebutuhan data transaksi, inventory, database customer, serta operasional publik marketplace secara real-time.

Aplikasi ini menerapkan arsitektur *nested-apps* modular untuk memisahkan setiap divisi bisnis guna menjaga skalabilitas, isolasi dependensi, dan kemudahan pemeliharaan kode (*maintainability*) jangka panjang.

**Live Catalog (Customer):** [demo.solutioncorp.id](https://demo.solutioncorp.id)  
**Internal Dashboard (Admin Panel):** [demo.solutioncorp.id/dashboard](https://demo.solutioncorp.id/dashboard)  

---

## Akses Demo (Dashboard)
Jika ingin menguji coba integrasi data pada *Live Dashboard*, silakan gunakan akun demo berikut pada halaman login:
* **Username:** `demo`
* **Password:** `admin123`

---

## Arsitektur & Fitur Utama Sistem

Sistem backend ini terbagi menjadi dua kelompok modul besar (*nested-apps*) untuk efisiensi bisnis:

### 1. Admin App (`admin_app`) - ERP & Dashboard Internal
* **Modul Finance (`admin_app.finance`):** Melakukan manajemen keuangan, pencatatan transaksi masuk/keluar, pelacakan **Omzet, Laba, dan Pengeluaran** perusahaan secara real-time.
* **Modul Inventory (`admin_app.inventory`):** Mengelola siklus ketersediaan stok barang baku hingga produk siap jual, lengkap dengan manajemen media upload gambar produk.
* **Modul Sales (`admin_app.sales`):** Mengelola basis data pelanggan (customer relationship management) dan riwayat penjualan tertaut.
* **Dashboard Control Core (`dashboard`):** Menangani routing dan logika backend khusus untuk portal karyawan.

### 2. Marketplace App (`marketplace_app`) - Customer Facing Portal
* **Modul Home (`marketplace_app.home`):** Menyediakan landing page data aggregator dan etalase utama yang ringan dikonsumsi oleh frontend.
* **Modul Product (`marketplace_app.product`):** Menampilkan katalog produk interaktif secara publik lengkap dengan integrasi static-media file.
* **Modul Checkout (`marketplace_app.checkout`):** Memproses alur validasi transaksi belanja dan penyiapan data invoice pelanggan sebelum dilempar ke divisi sales.

---


* **Language & Framework:** Python 3.x | Django 5.x | Django REST Framework (DRF)
* **Authentication:** `django-rest-framework-simplejwt` (Sistem autentikasi berbasis stateless JWT Token dengan *Access Token Lifetime* selama 12 jam dan otomatisasi *Refresh Token Rotation*).
* **Database Dual-State:** * **Production:** PostgreSQL (Docker-ready Environment)
  * **Development/Local:** SQLite 3
* **Middleware & Security:** * `django-cors-headers` untuk mengamankan komunikasi lintas port dari origin resmi frontend (`https://solutioncorp.id` & localhost).
  * `CSRF_TRUSTED_ORIGINS` terintegrasi dengan proteksi Cloudflare HTTPS.
* **Localization:** Waktu sistem disesuaikan ke Zona Waktu lokal (`Asia/Jakarta`) agar pencatatan *timestamp* pada invoice sales dan laporan keuangan sinkron dengan jam operasional riil di Indonesia.

---
 Repositori
```bash
git clone [https://github.com/AdamPerdana/solutioncorp-backend.git](https://github.com/AdamPerdana/solutioncorp-backend.git)
cd solutioncorp-backend

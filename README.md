# SolutionCorp Backend - Sistem Manajemen Bisnis ERP

Proyek backend untuk sistem manajemen bisnis PT Solution Corp Indonesia. Sistem ini dibangun menggunakan Django Rest Framework (DRF) untuk memfasilitasi kebutuhan data transaksi, inventory, database customer, serta pengelolaan mini marketplace secara real-time.

Aplikasi ini menerapkan arsitektur nested-apps modular untuk memisahkan setiap divisi bisnis guna menjaga skalabilitas dan kemudahan pemeliharaan kode (maintainability) dalam jangka panjang.

## Fitur Utama Sistem

1. Modul Sales dan Customer (admin_app.sales): Mengelola data pelanggan dan pelacakan transaksi secara real-time.
2. Manajemen Database Relasional: Menggunakan ORM Django untuk operasi CRUD (Create, Read, Update, Delete) yang aman dan terstruktur.
3. Integrasi API Gateway: Serialisasi data dalam format JSON menggunakan Django REST Serializers untuk konsumsi Frontend (React.js).
4. Keamanan CORS: Konfigurasi menggunakan django-cors-headers untuk mengamankan komunikasi lintas port antara client dan server.
5. Kesiapan Mini Marketplace: Perancangan arsitektur database yang siap disinkronisasikan dengan multi-channel toko digital.

## Spesifikasi Teknologi

- Language: Python 3.x
- Framework: Django 5.x
- API Toolkit: Django REST Framework
- Database: SQLite (Development) / PostgreSQL Ready
- Middleware: Django CORS Headers

## Panduan Instalasi dan Pengoperasian Lokal

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di lingkungan lokal:

### 1. Kloning Repositori
```bash
git clone [https://github.com/USERNAME_KAMU/solutioncorp-backend.git](https://github.com/AdamPerdana/solutioncorp-backend.git)
cd solutioncorp-backend

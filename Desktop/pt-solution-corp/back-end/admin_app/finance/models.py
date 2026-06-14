from django.db import models


# ==========================================================
# [PIUTANG DAGANG (ACCOUNTS RECEIVABLE)]
# ==========================================================
class Piutang(models.Model):
    STATUS_PIUTANG_CHOICES = [
        ('Belum Lunas', 'Belum Lunas'),
        ('Cicilan', 'Cicilan / Dibayar Sebagian'),
        ('Lunas', 'Lunas'),
    ]

    nomor_invoice = models.CharField(max_length=100, unique=True)  # Kunci faktur POS dari aplikasi Sales
    pelanggan = models.CharField(max_length=255)  # Sinkronisasi nama toko/instansi pembeli
    tanggal_transaksi = models.DateField()  # Tanggal awal pembukuan transaksi kasir POS
    jatuh_tempo = models.DateField()  # Batas akhir credit line (Term of Payment) yang dihitung otomatis

    total_tagihan = models.BigIntegerField()  # Nilai grand total kotor awal nota transaksi tempo
    sisa_piutang = models.BigIntegerField()  # Saldo sisa piutang berjalan yang wajib ditagih ke customer

    status_piutang = models.CharField(
        max_length=50,
        choices=STATUS_PIUTANG_CHOICES,
        default="Belum Lunas"
    )

    created_at = models.DateTimeField(auto_now_add=True)  # Waktu otomatis pencatatan masuk sistem finansial

    class Meta:
        db_table = 'finance_piutang'
        ordering = [
            'jatuh_tempo']  # Mengurutkan otomatis berdasarkan tanggal jatuh tempo terdekat (Prioritas Penagihan)

    def __str__(self):
        return f"[{self.nomor_invoice}] - {self.pelanggan} (Sisa: Rp {self.sisa_piutang:,})"
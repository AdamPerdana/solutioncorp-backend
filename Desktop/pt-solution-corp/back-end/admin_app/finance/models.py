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

    nomor_invoice = models.CharField(max_length=100, unique=True)
    pelanggan = models.CharField(max_length=255)
    tanggal_transaksi = models.DateField()
    jatuh_tempo = models.DateField()

    total_tagihan = models.BigIntegerField()
    sisa_piutang = models.BigIntegerField()

    status_piutang = models.CharField(
        max_length=50,
        choices=STATUS_PIUTANG_CHOICES,
        default="Belum Lunas"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_piutang'
        ordering = [
            'jatuh_tempo']  #

    def __str__(self):
        return f"[{self.nomor_invoice}] - {self.pelanggan} (Sisa: Rp {self.sisa_piutang:,})"


# ==========================================================
# [HUTANG DAGANG (ACCOUNTS PAYABLE)]
# ==========================================================
class Hutang(models.Model):
    STATUS_HUTANG_CHOICES = [
        ('Belum Lunas', 'Belum Lunas'),
        ('On Process', 'On Process'),
        ('Lunas', 'Lunas'),
    ]

    nomor_po = models.CharField(max_length=100, unique=True)
    supplier = models.CharField(max_length=255)
    tanggal_po = models.DateField()
    deskripsi_barang = models.TextField(blank=True, null=True)

    total_tagihan = models.BigIntegerField()
    sisa_hutang = models.BigIntegerField()

    status_hutang = models.CharField(
        max_length=50,
        choices=STATUS_HUTANG_CHOICES,
        default="Belum Lunas"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_hutang'
        ordering = [
            'tanggal_po']

    def __str__(self):
        return f"[{self.nomor_po}] - {self.supplier} (Sisa: Rp {self.sisa_hutang:,})"


# ==========================================================
# [ MODEL FINANCE: BIAYA OPERASIONAL ]
# ==========================================================
class Biaya(models.Model):
    METODE_CHOICES = [
        ('Tunai / Kas Kecil', 'Tunai / Kas Kecil'),
        ('Transfer Bank', 'Transfer Bank'),
    ]

    tanggal = models.DateField()
    kategori = models.CharField(max_length=100)
    metode = models.CharField(max_length=50, choices=METODE_CHOICES, default='Tunai / Kas Kecil')
    nominal = models.BigIntegerField()
    keterangan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.kategori}] {self.keterangan[:30]} - Rp {self.nominal}"
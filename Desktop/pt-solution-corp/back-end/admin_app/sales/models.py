from django.db import models


# ==========================================================
# [CUSTOMER ]
# ==========================================================
class Customer(models.Model):
    nama = models.CharField(max_length=250, unique=True)
    kontak = models.CharField(max_length=250, default="-", blank=True)
    telepon = models.CharField(max_length=50, default="-", blank=True)
    alamat = models.TextField(blank=True, default="-")
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.nama


# ==========================================================
# [ INVOICE PROFORMA]
# ==========================================================
class ProformaInvoice(models.Model):
    nomor_invoice = models.CharField(max_length=50)
    pelanggan = models.CharField(max_length=255)
    alamat_pengiriman = models.TextField(blank=True, default="Jakarta")
    tanggal = models.DateField()
    ongkir = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proforma_invoice'
        ordering = ['-created_at']  # Menampilkan invoice terbaru urutan teratas

    def __str__(self):
        return f"{self.nomor_invoice} - {self.pelanggan}"


class ProformaInvoiceItem(models.Model):
    invoice = models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE, related_name='items')
    sku = models.CharField(max_length=50)
    nama_produk = models.CharField(max_length=255)
    qty = models.IntegerField()
    harga = models.IntegerField()
    total = models.IntegerField()  # Hasil kalkulasi (qty * harga) dari POS

    class Meta:
        db_table = 'proforma_invoice_item'

    def __str__(self):
        return f"{self.sku} x {self.qty}"


# ==========================================================
# [ POINT OF SALES (POS TRANSACTION)]
# ==========================================================
class PosTransaction(models.Model):
    METODE_CHOICES = [
        ('TUNAI', 'Tunai'),
        ('TEMPO/KREDIT', 'Tempo/Kredit'),
    ]
    STATUS_CHOICES = [
        ('Lunas', 'Lunas'),
        ('Tempo', 'Tempo'),
    ]

    nomor_invoice = models.CharField(max_length=50, unique=True)  # Terkunci unik agar tidak ada nomor nota ganda
    pelanggan = models.CharField(max_length=150)
    alamat = models.TextField(blank=True, null=True)
    tanggal = models.DateField()
    metode_bayar = models.CharField(max_length=20, choices=METODE_CHOICES, default='TUNAI')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Lunas')
    ongkir = models.IntegerField(default=0)
    grand_total = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nomor_invoice} - {self.pelanggan}"


class PosTransactionItem(models.Model):
    transaksi = models.ForeignKey(PosTransaction, on_delete=models.CASCADE, related_name='items')
    sku = models.CharField(max_length=30)
    nama_produk = models.CharField(max_length=200)
    qty = models.IntegerField()
    harga = models.IntegerField()
    total = models.BigIntegerField()

    def __str__(self):
        return f"{self.sku} ({self.qty} pcs)"
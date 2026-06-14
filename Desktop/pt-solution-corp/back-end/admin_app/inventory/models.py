from django.db import models
from django.utils import timezone


# ==========================================================
# [PRODUCT]
# ==========================================================
class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)  # Kode unik barang (misal: PXTON-GEL-01)
    nama = models.CharField(max_length=200)
    min_stok = models.IntegerField(default=0)
    satuan = models.CharField(max_length=50, default='Pcs')

    stok_aktual = models.IntegerField(default=0)  # Nilai stok otomatis terpotong saat transaksi POS
    hpp = models.IntegerField(default=0)  # Harga Pokok Pembelian untuk kalkulasi margin profit
    harga_jual = models.IntegerField(default=0)  # Harga jual standar dari otomatis mesin POS Kasir

    def __str__(self):
        return f"[{self.sku}] {self.nama}"


# ==========================================================
# [ SUPPLIER ]
# ==========================================================
class Supplier(models.Model):
    nama = models.CharField(max_length=255, unique=True)
    kontak = models.CharField(max_length=255, blank=True, default="-")
    telepon = models.CharField(max_length=50, null=True, blank=True, default="-")
    rekening = models.CharField(max_length=255, null=True, blank=True, default="-")
    alamat = models.TextField(null=True, blank=True, default="-")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama

    class Meta:
        ordering = ['-id']  # Menampilkan supplier baru di urutan teratas


# ==========================================================
# [ PURCHASE ORDER ]
# ==========================================================
class PurchaseOrder(models.Model):
    nomor_po = models.CharField(max_length=100, unique=True)  # Nomor urut dokumen PO belanja
    supplier = models.CharField(max_length=255)  # Menyimpan nama supplier terpilih
    tanggal = models.DateField(default=timezone.now)
    grand_total = models.BigIntegerField(default=0)  # Total akumulasi nilai belanja
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nomor_po

    class Meta:
        ordering = ['-id']


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    sku = models.CharField(max_length=100)
    nama_produk = models.CharField(max_length=255)
    qty = models.IntegerField(default=1)
    harga_beli = models.BigIntegerField(default=0)
    total = models.BigIntegerField(default=0)  # Hasil kalkulasi (qty * harga_beli)

    def __str__(self):
        return f"{self.sku} - {self.purchase_order.nomor_po}"
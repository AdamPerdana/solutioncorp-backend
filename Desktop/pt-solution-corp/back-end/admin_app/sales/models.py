from django.db import models

#Customer
class Customer(models.Model):
    nama = models.CharField(max_length = 250, unique = True)
    kontak = models.CharField(max_length = 250, unique = True, default="-", blank=True)
    telepon = models.CharField(max_length = 50, unique = True, default="-",blank=True)
    alamat = models.TextField(max_length = 100, blank=True, default="-")
    created_at = models.DateTimeField(auto_now_add=True)

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.nama

#INVOICE PROFORMA
class ProformaInvoice(models.Model):
    nomor_invoice = models.CharField(max_length=50,)
    pelanggan = models.CharField(max_length=255)
    alamat_pengiriman = models.TextField(blank=True, default="Jakarta")
    tanggal = models.DateField()
    ongkir = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proforma_invoice'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nomor_invoice} - {self.pelanggan}"


class ProformaInvoiceItem(models.Model):
    invoice = models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE, related_name='items')
    sku = models.CharField(max_length=50)
    nama_produk = models.CharField(max_length=255)
    qty = models.IntegerField()
    harga = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'proforma_invoice_item'

    def __str__(self):
        return f"{self.sku} x {self.qty}"



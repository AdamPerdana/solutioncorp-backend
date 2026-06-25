from django.db import models
from marketplace_app.product.models import Product  # Ambil database product sebagai relasi

class Order(models.Model):
    customer_name = models.CharField(max_length=30, verbose_name="Nama Pembeli")
    customer_whatsapp = models.CharField(max_length=14, verbose_name="No. WhatsApp")
    shipping_region = models.CharField(max_length=100, verbose_name="Wilayah Pengiriman")
    courier_service = models.CharField(max_length=50, verbose_name="Layanan Kurir")
    status = models.CharField(max_length=30, default="Pending/WhatsApp", verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Masuk")

    def __str__(self):
        return f"Leads #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Produk")
    quantity = models.IntegerField(verbose_name="Jumlah (Qty)")
    price_at_purchase = models.IntegerField(verbose_name="Harga Saat Transaksi")

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Produk Dihapus'}"
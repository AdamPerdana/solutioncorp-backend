from django.db import models
from django.utils.text import slugify

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nama Produk")
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name="Slug URL")
    price = models.IntegerField(verbose_name="Harga")
    image = models.ImageField(upload_to='', verbose_name="Foto Utama")
    stock_quantity = models.IntegerField(default=0, verbose_name="Stok")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='', verbose_name="Foto Tambahan")

    def __str__(self):
        return f"Foto Tambahan untuk {self.product.name}"

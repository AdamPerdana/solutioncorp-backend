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




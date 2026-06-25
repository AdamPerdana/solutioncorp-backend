from rest_framework import serializers
from .models import Order, OrderItem
from marketplace_app.product.models import Product
import re


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price_at_purchase']


class CheckoutSerializer(serializers.ModelSerializer):
    # Menangani array produk di keranjang
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_whatsapp', 'shipping_region', 'courier_service', 'items']

    # 1. Validasi Field customer_name (Maksimal 30 huruf & spasi)
    def validate_customer_name(self, value):
        if len(value) > 30:
            raise serializers.ValidationError("Nama lengkap maksimal 30 karakter.")

        # Regex memastikan tidak ada angka, simbol, atau kode skrip
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Nama hanya boleh mengandung huruf dan spasi.")

        return value

    # 2. Validasi  Field customer_whatsapp (Maksimal 14 digit, Wajib Awalan 08 / 628)
    def validate_customer_whatsapp(self, value):
        # Bersihkan semua karakter non-angka jika ada yang lolos atau ditembak langsung via API
        digits_only = re.sub(r'[^0-9]', '', value)

        if not (9 <= len(digits_only) <= 14):
            raise serializers.ValidationError("Nomor harus terdiri dari 9 hingga 14 digit angka.")

        if not digits_only.startswith(('08', '628')):
            raise serializers.ValidationError("Nomor telepon tidak valid.")

        return digits_only

    # 3. Logika Pembuatan Data Transaksi Berlapis
    def create(self, validated_data):
        # Pisahkan data item keranjang dari data utama pembeli
        items_data = validated_data.pop('items')

        # Simpan data pembeli ke tabel Order setelah lolos validasi di atas
        order = Order.objects.create(**validated_data)

        # Simpan semua produk di keranjang ke tabel OrderItem
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order
from rest_framework import serializers
from .models import Customer, ProformaInvoice, ProformaInvoiceItem, PosTransaction, PosTransactionItem
from admin_app.inventory.models import Product


# ==========================================================
# [ CUSTOMER ]
# ==========================================================
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'nama', 'kontak', 'telepon', 'alamat']


# ==========================================================
# [INVOICE PROFORMA]
# ==========================================================
class ProformaInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoiceItem
        fields = ['id', 'sku', 'nama_produk', 'qty', 'harga', 'total']


class ProformaInvoiceSerializer(serializers.ModelSerializer):
    items = ProformaInvoiceItemSerializer(many=True)

    class Meta:
        model = ProformaInvoice
        fields = ['id', 'nomor_invoice', 'pelanggan', 'alamat_pengiriman', 'tanggal', 'ongkir', 'items', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        invoice = ProformaInvoice.objects.create(**validated_data)

        for item_data in items_data:
            ProformaInvoiceItem.objects.create(invoice=invoice, **item_data)

        return invoice


# ==========================================================
# [ POINT OF SALES (POS)]
# ==========================================================
class PosTransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosTransactionItem
        fields = ['sku', 'nama_produk', 'qty', 'harga', 'total']


class PosTransactionSerializer(serializers.ModelSerializer):
    items = PosTransactionItemSerializer(many=True)

    omset_murni = serializers.SerializerMethodField()

    class Meta:
        model = PosTransaction
        fields = [
            'id', 'nomor_invoice', 'pelanggan', 'alamat', 'tanggal',
            'metode_bayar', 'status', 'ongkir', 'grand_total', 'omset_murni', 'items'
        ]

    def get_omset_murni(self, obj):
        total_kotor = obj.grand_total or 0
        nominal_ongkir = obj.ongkir or 0
        return total_kotor - nominal_ongkir

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        transaksi = PosTransaction.objects.create(**validated_data)

        for item_data in items_data:
            PosTransactionItem.objects.create(transaksi=transaksi, **item_data)

            try:
                product = Product.objects.get(sku=item_data['sku'])
                product.stok_aktual -= item_data['qty']
                product.save()

            except Product.DoesNotExist:
                print(f"Peringatan: SKU {item_data['sku']} tidak ditemukan di database gudang. Stok gagal dipotong.")

        return transaksi
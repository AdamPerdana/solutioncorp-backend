from rest_framework import serializers
from .models import Customer,ProformaInvoice,ProformaInvoiceItem

#CUSTOMER
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id','nama','kontak','telepon','alamat']

#INVOICE PROFORMA
from rest_framework import serializers
from .models import ProformaInvoice, ProformaInvoiceItem

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
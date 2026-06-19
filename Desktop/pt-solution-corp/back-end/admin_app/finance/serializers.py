from rest_framework import serializers
from .models import Piutang, Hutang, Biaya

# ==========================================================
# [SERIALIZER PIUTANG ]
# ==========================================================
class PiutangSerializer(serializers.ModelSerializer):
    class Meta:
        model = Piutang
        fields = [
            'id', 'nomor_invoice', 'pelanggan', 'tanggal_transaksi',
            'jatuh_tempo', 'total_tagihan', 'sisa_piutang', 'status_piutang'
        ]


# ==========================================================
# [SERIALIZER HUTANG ]
# ==========================================================
from admin_app.inventory.models import PurchaseOrder, PurchaseOrderItem


class HutangPOItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ['sku', 'nama_produk', 'qty', 'harga_beli', 'total']


class HutangSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Hutang

        fields = [
            'id', 'nomor_po', 'supplier', 'tanggal_po',
            'deskripsi_barang', 'total_tagihan', 'sisa_hutang', 'status_hutang', 'items'
        ]


    def get_items(self, obj):
        try:
            po_induk = PurchaseOrder.objects.get(nomor_po=obj.nomor_po)
            qs_items = po_induk.items.all()

            return HutangPOItemSerializer(qs_items, many=True).data
        except PurchaseOrder.DoesNotExist:
            return []

        
# ==========================================================
# [ SERIALIZER FINANCE: BIAYA ]
# ==========================================================
class BiayaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Biaya
        fields = ['id', 'tanggal', 'kategori', 'metode', 'nominal', 'keterangan']
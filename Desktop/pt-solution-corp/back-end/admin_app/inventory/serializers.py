import logging
from django.db import transaction
from rest_framework import serializers

# MODELS INTERNAL MODUL INVENTORY
from .models import Product, Supplier, PurchaseOrder, PurchaseOrderItem
# MODELS EKSTERNAL MODUL FINANCE
from admin_app.finance.models import Hutang

logger = logging.getLogger(__name__)


# ==========================================================
# [SERIALIZER PRODUCT]
# ==========================================================
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'nama', 'min_stok', 'satuan', 'stok_aktual', 'hpp', 'harga_jual']


# ==========================================================
# [SERIALIZER SUPPLIER]
# ==========================================================
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'nama', 'kontak', 'telepon', 'rekening', 'alamat']


# ==========================================================
# [SERIALIZER PURCHASE ORDER ITEMS]
# ==========================================================
class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ['sku', 'nama_produk', 'qty', 'harga_beli', 'total']


# ==========================================================
# [SERIALIZER MAIN PURCHASE ORDER]
# ==========================================================
class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)
    status_hutang = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'nomor_po', 'supplier', 'tanggal', 'grand_total', 'items', 'status_hutang']


    def get_status_hutang(self, obj):
        try:
            hutang_record = Hutang.objects.filter(nomor_po__iexact=str(obj.nomor_po).strip()).first()
            if hutang_record:
                return hutang_record.status_hutang
        except Exception as e:
            logger.error("Gagal membaca status hutang untuk PO %s: %s", obj.nomor_po, str(e))
        return "Belum Lunas"


    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        deskripsi_buffer = []


        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=purchase_order, **item_data)

            current_sku = item_data.get('sku')
            qty_input = item_data.get('qty', 0)
            harga_beli_baru = item_data.get('harga_beli', 0)
            nama_produk = item_data.get('nama_produk') or "Item Bahan Baku"

            deskripsi_buffer.append(f"{qty_input} Pcs {nama_produk}")

            try:
                target_product = Product.objects.get(sku=current_sku)
                target_product.stok_aktual += qty_input
                target_product.hpp = harga_beli_baru
                target_product.save()

            except Product.DoesNotExist:
                print(f"Peringatan: SKU {current_sku} tidak terdaftar di master inventori. Mutasi stok & HPP dilewati.")
                continue

        deskripsi_final = ", ".join(deskripsi_buffer) if deskripsi_buffer else "Pembelian Bahan Baku Stok"


        Hutang.objects.create(
            nomor_po=purchase_order.nomor_po,
            supplier=purchase_order.supplier,
            tanggal_po=purchase_order.tanggal,
            deskripsi_barang=deskripsi_final,
            total_tagihan=purchase_order.grand_total,
            sisa_hutang=purchase_order.grand_total,
            status_hutang="Belum Lunas"
        )

        return purchase_order
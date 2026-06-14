from rest_framework import serializers
from .models import Product, Supplier, PurchaseOrder, PurchaseOrderItem

# ==========================================================
# [SERIALIZER  PRODUCT]
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
# [SERIALIZER PURCHASE ORDER]
# ==========================================================
class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ['sku', 'nama_produk', 'qty', 'harga_beli', 'total']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'nomor_po', 'supplier', 'tanggal', 'grand_total', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=purchase_order, **item_data)

            current_sku = item_data.get('sku')
            qty_input = item_data.get('qty', 0)
            harga_beli_baru = item_data.get('harga_beli', 0)  # Nilai harga beli ter-update dari vendor

            try:
                # Cari produk  di Master Product berdasarkan kode SKU
                target_product = Product.objects.get(sku=current_sku)

                #  MUTASI TAMBAH STOK: Akumulasikan volume stok_aktual lama gudang dengan Qty masuk dari PO baru
                target_product.stok_aktual += qty_input

                #  OVERRIDE VALUE HPP: Timpa nilai HPP master produk lama secara real-time dengan harga PO yang baru masuk
                target_product.hpp = harga_beli_baru

                # simpan seluruh perubahan parameter master produk ke database gudang
                target_product.save()

            except Product.DoesNotExist:
                # Jika kasir/admin menulis manual SKU yang tidak ada di master inventori,
                # proses simpan PO tetap berjalan tanpa mematahkan interupsi sistem (Fail-Safe)
                print(f"Peringatan: SKU {current_sku} tidak terdaftar di master inventori. Mutasi stok & HPP dilewati.")
                continue

        # 4. Selesai. Kembalikan paket objek dokumen Purchase Order yang telah dibukukan
        return purchase_order
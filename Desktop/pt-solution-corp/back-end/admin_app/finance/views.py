import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Piutang
from .serializers import PiutangSerializer

# CROSS-APP COUPLING: Hubungkan model transaksi POS dari aplikasi Sales
from admin_app.sales.models import PosTransaction

logger = logging.getLogger(__name__)

# ==========================================================
# [ FINANCE: PIUTANG ]
# ==========================================================
class PiutangViewSet(viewsets.ModelViewSet):
    # Menyusun daftar invoice tempo diurutkan dari yang terbaru dibukukan
    queryset = Piutang.objects.all().order_by('-id')
    serializer_class = PiutangSerializer

    # ==========================================================
    # Override GET Detail (ID) Menarik Item POS
    # ==========================================================
    def retrieve(self, request, *args, **kwargs):
        # 1. Ambil data record piutang utama berdasarkan parameter ID di URL
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data_piutang = serializer.data

        # 2. CROSS-DATABASE QUERY: Lacak invoice POS penjualan yang memicu piutang ini berdasarkan nomor_invoice
        transaksi_pos = PosTransaction.objects.filter(nomor_invoice=instance.nomor_invoice).first()

        # buffer penampung data eksternal aplikasi Sales
        items_data = []
        alamat_pengiriman = "Jakarta"  # Nilai standard fallback alamat jika tidak terlacak

        # 3.Jika invoice POS ditemukan, ambil data logistik and rincian produknya
        if transaksi_pos:
            # Ambil alamat pengiriman riil dari POS saat transaksi
            alamat_pengiriman = transaksi_pos.alamat

            # untuk memetakan seluruh baris barang yang terikat di nota penjualan (PosTransactionItem)
            for item in transaksi_pos.items.all():
                items_data.append({
                    'sku': item.sku,
                    'nama_produk': item.nama_produk,
                    'qty': item.qty,
                    'harga': item.harga,
                    'total': item.total
                })

        # 4.   array items dan string alamat ke dalam data serialier utama
        data_piutang['alamat'] = alamat_pengiriman
        data_piutang['items'] = items_data

        return Response(data_piutang, status=status.HTTP_200_OK)
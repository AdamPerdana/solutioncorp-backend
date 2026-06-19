import logging
from datetime import datetime
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

#  MODELS FINANCE
from .models import Piutang, Hutang, Biaya
from .serializers import PiutangSerializer, HutangSerializer, BiayaSerializer

# CROSS-APP COUPLING: Hubungkan model transaksi POS & PO dari aplikasi pasangannya
from admin_app.sales.models import PosTransaction
from admin_app.inventory.models import PurchaseOrder

logger = logging.getLogger(__name__)


# ==========================================================
# [ VIEWSET FINANCE: PIUTANG DAGANG ]
# ==========================================================
class PiutangViewSet(viewsets.ModelViewSet):
    queryset = Piutang.objects.all().order_by('-id')
    serializer_class = PiutangSerializer

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Dilarang keras! Penghapusan piutang hanya boleh dieksekusi satu pintu melalui Laporan Sales."},
            status=status.HTTP_403_FORBIDDEN
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data_piutang = serializer.data

        transaksi_pos = PosTransaction.objects.filter(nomor_invoice=instance.nomor_invoice).first()

        items_data = []
        alamat_pengiriman = "Jakarta"

        if transaksi_pos:
            alamat_pengiriman = transaksi_pos.alamat
            for item in transaksi_pos.items.all():
                items_data.append({
                    'sku': item.sku,
                    'nama_produk': item.nama_produk,
                    'qty': item.qty,
                    'harga': item.harga,
                    'total': item.total
                })

        data_piutang['alamat'] = alamat_pengiriman
        data_piutang['items'] = items_data

        return Response(data_piutang, status=status.HTTP_200_OK)


# ==========================================================
# [VIEWSET FINANCE:  HUTANG DAGANG ]
# ==========================================================
class HutangViewSet(viewsets.ModelViewSet):
    queryset = Hutang.objects.all().order_by('status_hutang', 'tanggal_po')
    serializer_class = HutangSerializer

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Akses ditolak! Pembatalan hutang dagang wajib dilakukan satu pintu melalui PO Report."},
            status=status.HTTP_403_FORBIDDEN
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data_hutang = serializer.data

        nomor_po_clean = str(instance.nomor_po).strip() if instance.nomor_po else ""
        po_induk = PurchaseOrder.objects.filter(nomor_po__iexact=nomor_po_clean).first()

        items_data = []

        if po_induk:
            for item in po_induk.items.all():
                items_data.append({
                    'sku': item.sku,
                    'nama_produk': item.nama_produk,
                    'qty': item.qty,
                    'harga_beli': item.harga_beli,
                    'total': item.total
                })
        else:
            logger.warning(f"Gagal cross-app query PO untuk Nomor: '{nomor_po_clean}' pada ID Hutang: {instance.id}")

        data_hutang['items'] = items_data
        return Response(data_hutang, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        status_baru = request.data.get('status_hutang', None)
        sisa_baru = request.data.get('sisa_hutang', None)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        logger.info(f"Mutasi Hutang Dokumen {instance.nomor_po}: Status={status_baru}, Sisa={sisa_baru}")
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==========================================================
# [ VIEWSET FINANCE: BIAYA OPERASIONAL ]
# ==========================================================
class BiayaViewSet(viewsets.ModelViewSet):
    queryset = Biaya.objects.all().order_by('-tanggal', '-id')
    serializer_class = BiayaSerializer

    def get_queryset(self):
        queryset = Biaya.objects.all().order_by('-tanggal', '-id')
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)


        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(tanggal__range=[start_dt, end_dt])
            except ValueError:
                pass
        return queryset

    @action(detail=False, methods=['get'], url_path='biaya-operational')
    def biaya_operational_rekap(self, request):
        biaya_tersaring = self.get_queryset()
        serializer = self.get_serializer(biaya_tersaring, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
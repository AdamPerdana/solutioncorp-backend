import logging
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

# MODELS INVENTORY & PURCHASING
from .models import PurchaseOrder, Product, Supplier
#  SERIALIZER
from .serializers import PurchaseOrderSerializer, ProductSerializer, SupplierSerializer
#  CETAK PDF UTILITY
from .utility import generate_po_pdf_output

logger = logging.getLogger(__name__)


# ==========================================================
# [ PRODUCT ]
# ==========================================================
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-id')
    serializer_class = ProductSerializer


# ==========================================================
# [ SUPPLIER ]
# ==========================================================
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


# ==========================================================
# [PURCHASE ORDER (PO)]
# ==========================================================
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer

    # FILTRASI DATA DINAMIS: Batasi data PO yang ditarik hanya yang terbit pada hari ini saja
    def get_queryset(self):
        hari_ini = timezone.now().date()
        return PurchaseOrder.objects.filter(tanggal=hari_ini).order_by('-id')

    # ==========================================================
    # Pembuatan PO Baru
    # ==========================================================
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("DETAIL EROR SERIALIZER PENGADAAN PO:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Proses simpan data
        purchase_order_obj = serializer.save()

        try:
            # Ambil baris item barang yang baru saja melekat pada objek PO
            items_queryset = purchase_order_obj.items.all()

            #  penyusun PDF Purchase Order
            pdf_string = generate_po_pdf_output(purchase_order_obj, items_queryset)

            # output string mentah ke dalam format biner latin-1 agar struktur file PDF tidak korup
            pdf_bytes = pdf_string.encode('latin-1')

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="PO_{purchase_order_obj.nomor_po}.pdf"'
            return response

        except Exception as error:
            # Jika PDF macet, data PO di database dipastikan aman dan server mengembalikan status 210
            logger.error("Gagal memproses cetakan file PDF Purchase Order: %s", str(error), exc_info=True)
            return Response(
                {
                    "message": "Data PO berhasil disimpan ke database, namun pembuatan file PDF terkendala.",
                    "id": purchase_order_obj.id
                },
                status=status.HTTP_210_CURRENT_CUSTODIAN_NON_CRITICAL_ERROR if hasattr(status,
                                                                                       'HTTP_210_CURRENT_CUSTODIAN_NON_CRITICAL_ERROR') else status.HTTP_201_CREATED
            )

    # ==========================================================
    # Hitung Counter Transaksi PO Berjalan Bulanan
    # ==========================================================
    @action(detail=False, methods=['get'], url_path='last-counter')
    def last_counter(self, request):
        tgl_sekarang = timezone.now()
        tahun = tgl_sekarang.year
        bulan = tgl_sekarang.month

        # Hitung kuantitas riil PO khusus pada bulan dan tahun berjalan ini
        jumlah_po_bulan_ini = PurchaseOrder.objects.filter(
            tanggal__year=tahun,
            tanggal__month=bulan
        ).count()

        return Response({'counter': jumlah_po_bulan_ini}, status=status.HTTP_200_OK)

    # ==========================================================
    #  Pembatalan / Eliminasi Dokumen PO dari Server
    # ==========================================================
    @action(detail=False, methods=['delete'], url_path='delete-by-po')
    def delete_by_po(self, request):
        nomor_po_target = request.query_params.get('po', None)

        if not nomor_po_target:
            return Response({'error': 'Parameter nomor PO wajib disertakan pada query.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            po_dokumen = PurchaseOrder.objects.get(nomor_po=nomor_po_target)
            po_dokumen.delete()

            return Response({'message': f'Sukses menghapus dokumen PO {nomor_po_target} dari sistem.'},
                            status=status.HTTP_200_OK)

        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Dokumen Purchase Order tidak ditemukan di database server.'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Gagal menghapus dokumen PO: %s", str(e), exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
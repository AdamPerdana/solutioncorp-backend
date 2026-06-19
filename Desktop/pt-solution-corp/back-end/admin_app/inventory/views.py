import logging
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

# MODELS INVENTORY & PURCHASING
from .models import PurchaseOrder, Product, Supplier, PoCounter
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


    def get_queryset(self):
        tampilkan_semua = self.request.query_params.get('all', 'false').lower() == 'true'
        if tampilkan_semua:
            return PurchaseOrder.objects.all().order_by('-id')
        hari_ini = timezone.now().date()
        return PurchaseOrder.objects.filter(tanggal=hari_ini).order_by('-id')

    # ==========================================================
    # 1. (AUTO-CREATE JIKA DATABASE KOSONG)
    # ==========================================================
    @action(detail=False, methods=['get'], url_path='last-counter')
    def last_counter(self, request):
        try:
            sekarang = timezone.now()
            counter_obj, created = PoCounter.objects.get_or_create(
                tahun=sekarang.year,
                bulan=sekarang.month,
                defaults={'nilai_counter': 10}
            )
            return Response({"counter": counter_obj.nilai_counter}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==========================================================
    # 2. PEMBUATAN PO BARU (SINKRONISASI COUPLING COUNTER & PDF)
    # ==========================================================
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("DETAIL EROR SERIALIZER PENGADAAN PO:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        purchase_order_obj = serializer.save()

        try:
            items_queryset = purchase_order_obj.items.all()

            tgl_po = purchase_order_obj.tanggal or timezone.now().date()
            counter_obj, created = PoCounter.objects.get_or_create(
                tahun=tgl_po.year,
                bulan=tgl_po.month,
                defaults={'nilai_counter': 10}
            )
            counter_obj.nilai_counter += 1
            counter_obj.save()

            pdf_string = generate_po_pdf_output(purchase_order_obj, items_queryset)
            pdf_bytes = pdf_string.encode('latin-1')

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="PO_{purchase_order_obj.nomor_po}.pdf"'
            return response

        except Exception as error:
            logger.error("Gagal memproses cetakan file PDF Purchase Order: %s", str(error), exc_info=True)
            return Response(
                {
                    "message": "Data PO berhasil disimpan ke database, namun pembuatan file PDF terkendala.",
                    "id": purchase_order_obj.id
                },
                status=status.HTTP_201_CREATED
            )

    # ==========================================================
    #  CETAK ULANG (REPRINT) PDF PO LAMA
    # ==========================================================
    @action(detail=False, methods=['get'], url_path=r'reprint-po/?')
    def reprint_po(self, request):
        nomor_po_target = request.query_params.get('po', None)

        if not nomor_po_target:
            return Response({'error': 'Parameter nomor PO (?po=...) wajib disertakan.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            po_dokumen = PurchaseOrder.objects.get(nomor_po__iexact=str(nomor_po_target).strip())
            items_queryset = po_dokumen.items.all()

            pdf_string = generate_po_pdf_output(po_dokumen, items_queryset)
            pdf_bytes = pdf_string.encode('latin-1')

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="PO_{po_dokumen.nomor_po}.pdf"'
            return response

        except PurchaseOrder.DoesNotExist:
            return Response({'error': f'Dokumen PO {nomor_po_target} tidak terdaftar di sistem.'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Gagal cetak ulang PDF PO: %s", str(e), exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==========================================================
    # 3. PEMBATALAN PO
    # ==========================================================
    @action(detail=False, methods=['delete'], url_path='delete-by-po')
    @transaction.atomic
    def delete_by_po(self, request):
        nomor_po_target = request.data.get('po', None)

        if not nomor_po_target:
            return Response({'error': 'Parameter nomor PO wajib disertakan pada request body.'},
                            status=status.HTTP_400_BAD_REQUEST)

        po_bersih = str(nomor_po_target).strip()

        try:
            po_dokumen = PurchaseOrder.objects.get(nomor_po__iexact=po_bersih)
            tgl_po = po_dokumen.tanggal

            from .models import PurchaseOrderItem
            items_belanjaan = PurchaseOrderItem.objects.filter(purchase_order=po_dokumen)

            if items_belanjaan.exists():
                for item in items_belanjaan:
                    try:
                        master_produk = Product.objects.get(sku=item.sku)
                        master_produk.stok_aktual -= item.qty
                        master_produk.save()
                        logger.info(f"Reverse Stok Sukses: SKU {item.sku} berkurang {item.qty} Pcs")
                    except Product.DoesNotExist:
                        continue


            from admin_app.finance.models import Hutang
            Hutang.objects.filter(nomor_po__icontains=po_bersih).delete()


            counter_obj = PoCounter.objects.filter(tahun=tgl_po.year, bulan=tgl_po.month).first()
            if counter_obj and counter_obj.nilai_counter > 10:
                counter_obj.nilai_counter -= 1
                counter_obj.save()


            po_dokumen.delete()

            return Response({
                'message': f'Sukses total! Dokumen PO {po_bersih}, penyesuaian stok gudang, dan ledger hutang berhasil dibersihkan.'
            }, status=status.HTTP_200_OK)

        except PurchaseOrder.DoesNotExist:

            from admin_app.finance.models import Hutang
            hutang_yatim = Hutang.objects.filter(nomor_po__icontains=po_bersih)

            if hutang_yatim.exists():
                hutang_yatim.delete()
                return Response({
                    'message': f'Dokumen PO sudah tidak ada, namun sisa hutang {po_bersih} di finance berhasil disapu bersih.'
                }, status=status.HTTP_200_OK)

            return Response({'error': f'Dokumen Purchase Order {po_bersih} tidak ditemukan di database.'},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error("Gagal master delete PO: %s", str(e), exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
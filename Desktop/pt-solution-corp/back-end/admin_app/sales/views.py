import json
import logging
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

#  MODELS SALES & APPS FINANCE
from .models import Customer, ProformaInvoice, PosTransaction
from admin_app.finance.models import Piutang

# SERIALIZER
from .serializers import CustomerSerializer, ProformaInvoiceSerializer, PosTransactionSerializer

# CETAK PDF UTILITY
from .utility import generate_proforma_pdf_output
from .utility import generate_pos_invoice_pdf_output
from .utility import generate_pos_surat_jalan_pdf_output

logger = logging.getLogger(__name__)

# ==========================================================
# [CUSTOMER]
# ==========================================================
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('id')
    serializer_class = CustomerSerializer


# ==========================================================
# [INVOICE PROFORMA ]
# ==========================================================
@method_decorator(gzip_page, name='dispatch')
class ProformaInvoiceViewSet(viewsets.ModelViewSet):
    queryset = ProformaInvoice.objects.all()
    serializer_class = ProformaInvoiceSerializer

    # ACTION: Ambil total transaksi bulan ini
    @action(detail=False, methods=['get'], url_path='last-counter')
    def last_counter(self, request):
        try:
            sekarang = timezone.now()
            jumlah_bulan_ini = ProformaInvoice.objects.filter(
                tanggal__year=sekarang.year,
                tanggal__month=sekarang.month
            ).count()
            return Response({"counter": jumlah_bulan_ini}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # METHOD: Interceptor simpan data penawaran baru sekaligus generate file PDF
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice_data = serializer.validated_data
            items_data = request.data.get('items', [])

            # Jalankan pembuat file PDF Proforma
            pdf_raw_string = generate_proforma_pdf_output(invoice_data, items_data)
            pdf_bytes = pdf_raw_string.encode('latin-1')

            # Lempar balik data PDF
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Length'] = str(len(pdf_bytes))
            response['Content-Disposition'] = f'attachment; filename="Proforma_{request.data.get("nomor_invoice")}.pdf"'
            return response
        except Exception as e:
            logger.error("Gagal memproses PDF Proforma: %s", str(e), exc_info=True)
            return Response(
                {"error": f"Gagal memproses dokumen PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==========================================================
# [ POINT OF SALES ]
# ==========================================================
class PosTransactionViewSet(viewsets.ModelViewSet):
    queryset = PosTransaction.objects.all().order_by('-created_at')
    serializer_class = PosTransactionSerializer

    #  FILTRASI DATA: Tampilkan data transaksi hari ini
    def get_queryset(self):
        queryset = PosTransaction.objects.all().order_by('-created_at')
        if self.request.query_params.get('all') == 'true':
            return queryset
        hari_ini = timezone.localdate()
        return queryset.filter(tanggal=hari_ini)

    # ACTION: Hitung counter total invoice POS
    @action(detail=False, methods=['get'], url_path='last-counter')
    def last_counter(self, request):
        try:
            sekarang = timezone.now()
            jumlah_bulan_ini = PosTransaction.objects.filter(
                tanggal__year=sekarang.year,
                tanggal__month=sekarang.month
            ).count()
            return Response({"counter": jumlah_bulan_ini}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ACTION: Hapus transaksi POS dari database
    @action(detail=False, methods=['delete'], url_path='delete-by-invoice')
    def delete_by_invoice(self, request):
        nomor_invoice = request.query_params.get('invoice')
        if not nomor_invoice:
            return Response({"error": "Parameter nomor invoice wajib disertakan."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            transaksi = PosTransaction.objects.get(nomor_invoice=nomor_invoice)
            transaksi.delete()  # cascading item transaksi otomatis terhapus
            return Response({"message": f"Transaksi {nomor_invoice} sukses dihapus."}, status=status.HTTP_200_OK)
        except PosTransaction.DoesNotExist:
            return Response({"error": "Data transaksi tidak ditemukan di database server."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  ACTION: Cetak Ulang Invoice Lama
    @action(detail=False, methods=['get'], url_path='reprint-invoice')
    def reprint_invoice(self, request):
        nomor_invoice = request.query_params.get('invoice')
        try:
            transaksi = PosTransaction.objects.get(nomor_invoice=nomor_invoice)
            alamat_pembeli = transaksi.alamat

            if not alamat_pembeli or alamat_pembeli == "Melalui Loket Kasir POS Proyek":
                customer_master = Customer.objects.filter(nama=transaksi.pelanggan).first()
                if customer_master and customer_master.alamat and customer_master.alamat != "-":
                    alamat_pembeli = customer_master.alamat
                else:
                    alamat_pembeli = "Melalui Loket Kasir POS Proyek"

            items_query = transaksi.items.all()
            items_data = [
                {
                    'sku': item.sku,
                    'nama_produk': item.nama_produk,
                    'qty': item.qty,
                    'harga': item.harga,
                    'total': item.total
                } for item in items_query
            ]

            payload_pdf = {
                'nomor_invoice': transaksi.nomor_invoice,
                'pelanggan': transaksi.pelanggan,
                'tanggal': transaksi.tanggal,
                'metode_bayar': transaksi.metode_bayar,
                'status': transaksi.status,
                'ongkir': transaksi.ongkir,
                'grand_total': transaksi.grand_total,
                'alamat_pengiriman': alamat_pembeli,
                'jatuh_tempo_react': transaksi.tanggal
            }

            pdf_raw_string = generate_pos_invoice_pdf_output(payload_pdf, items_data)
            pdf_bytes = pdf_raw_string.encode('latin-1')

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Invoice_{transaksi.nomor_invoice}.pdf"'
            return response
        except Exception as e:
            logger.error("Gagal cetak ulang invoice POS: %s", str(e), exc_info=True)
            return Response({"error": "Terjadi kesalahan internal pada server database."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  ACTION: Cetak Surat Jalan Berdasarkan Nomor Invoice
    @action(detail=False, methods=['get'], url_path='print-surat-jalan')
    def print_surat_jalan(self, request):
        nomor_invoice = request.query_params.get('invoice')
        try:
            transaksi = PosTransaction.objects.get(nomor_invoice=nomor_invoice)
            alamat_pembeli = transaksi.alamat

            if not alamat_pembeli or alamat_pembeli == "Melalui Loket Kasir POS Proyek":
                customer_master = Customer.objects.filter(nama=transaksi.pelanggan).first()
                if customer_master and customer_master.alamat and customer_master.alamat != "-":
                    alamat_pembeli = customer_master.alamat
                else:
                    alamat_pembeli = "Melalui Loket Kasir POS Proyek"

            items_query = transaksi.items.all()
            items_data = [
                {
                    'sku': item.sku,
                    'nama_produk': item.nama_produk,
                    'qty': item.qty
                } for item in items_query
            ]

            payload_pdf = {
                'nomor_invoice': transaksi.nomor_invoice,
                'pelanggan': transaksi.pelanggan,
                'tanggal': transaksi.tanggal,
                'metode_bayar': transaksi.metode_bayar,
                'alamat_pengiriman': alamat_pembeli
            }

            pdf_raw_string = generate_pos_surat_jalan_pdf_output(payload_pdf, items_data)
            pdf_bytes = pdf_raw_string.encode('latin-1')

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="SuratJalan_{transaksi.nomor_invoice}.pdf"'
            return response
        except Exception as e:
            logger.error("Gagal mencetak surat jalan POS: %s", str(e), exc_info=True)
            return Response({"error": "Terjadi kesalahan internal pada server database."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  METHOD: Interceptor Kasir POS Utama
    def create(self, request, *args, **kwargs):
        alamat_pengiriman = request.data.get('alamat', 'Melalui Loket Kasir POS Proyek')
        jatuh_tempo_react = request.data.get('jatuhTempo')

        data = {
            'nomor_invoice': request.data.get('nomorInvoice'),
            'pelanggan': request.data.get('pelanggan'),
            'alamat': alamat_pengiriman,
            'tanggal': request.data.get('tanggal'),
            'metode_bayar': request.data.get('metodeBayar'),
            'status': request.data.get('status'),
            'ongkir': request.data.get('ongkir'),
            'grand_total': request.data.get('grandTotal'),
            'items': [
                {
                    'sku': item.get('sku'),
                    'nama_produk': item.get('nama'),
                    'qty': int(item.get('qty', 0)),
                    'harga': int(item.get('harga', 0)),
                    'total': int(item.get('total', 0))
                }
                for item in request.data.get('items', [])
            ]
        }

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("DETAIL EROR SERIALIZER PENJUALAN:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Simpan records transaksi POS utama (Sekaligus otomatis memotong stok gudang )
            self.perform_create(serializer)

            #  2. INTERCEPTOR PIUTANG: Cek jika transaksi bertipe non-tunai/tempo
            if data['metode_bayar'] == "TEMPO/KREDIT":
                try:
                    # Otomatis catat mutasi invoice kredit baru ke dalam ledger modul Piutang Finance
                    Piutang.objects.get_or_create(
                        nomor_invoice=data['nomor_invoice'],
                        defaults={
                            'pelanggan': data['pelanggan'],
                            'tanggal_transaksi': data['tanggal'],
                            'jatuh_tempo': jatuh_tempo_react if jatuh_tempo_react else data['tanggal'],
                            'total_tagihan': data['grand_total'],
                            'sisa_piutang': data['grand_total'],
                            'status_piutang': "Belum Lunas"
                        }
                    )
                except Exception as piutang_err:
                    # Fail-Safe: Log error finansial piutang tanpa merusak/menggagalkan cetakan nota di kasir
                    logger.error("Gagal mencatat mutasi piutang otomatis pada ledger finance: %s", str(piutang_err))

            # 3. Proses kompilasi rendering berkas stream biner PDF Invoice Komersial resmi
            payload_pdf = {
                'nomor_invoice': data['nomor_invoice'],
                'pelanggan': data['pelanggan'],
                'tanggal': data['tanggal'],
                'metode_bayar': data['metode_bayar'],
                'status': data['status'],
                'ongkir': data['ongkir'],
                'grand_total': data['grand_total'],
                'alamat_pengiriman': data['alamat'],
                'jatuh_tempo_react': jatuh_tempo_react
            }

            pdf_raw_string = generate_pos_invoice_pdf_output(payload_pdf, data['items'])
            pdf_bytes = pdf_raw_string.encode('latin-1')

            # Kirim balik stream byte PDF agar kasir otomatis mendownload struk lembar A4 transaksi
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Length'] = str(len(pdf_bytes))
            response['Content-Disposition'] = f'attachment; filename="Invoice_{data["nomor_invoice"]}.pdf"'
            return response
        except Exception as e:
            logger.error("Gagal memproses transaksi kasir POS: %s", str(e), exc_info=True)
            return Response({"error": "Terjadi kesalahan internal pada server database."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
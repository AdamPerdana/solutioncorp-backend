import json
import logging
from datetime import datetime
from django.db import transaction
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


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice_data = serializer.validated_data
            items_data = request.data.get('items', [])


            pdf_raw_string = generate_proforma_pdf_output(invoice_data, items_data)
            pdf_bytes = pdf_raw_string.encode('latin-1')


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


    def get_queryset(self):
        queryset = PosTransaction.objects.all().order_by('-created_at')
        if self.request.query_params.get('all') == 'true':
            return queryset
        hari_ini = timezone.localdate()
        return queryset.filter(tanggal=hari_ini)


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


    @action(detail=False, methods=['delete'], url_path='delete-by-invoice')
    @transaction.atomic
    def delete_by_invoice(self, request):
        nomor_invoice = request.data.get('invoice')

        if not nomor_invoice:
            return Response({"error": "Parameter nomor invoice wajib disertakan pada request body."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            transaksi = PosTransaction.objects.get(nomor_invoice=nomor_invoice)


            if hasattr(transaksi, 'items'):
                from admin_app.inventory.models import Product
                for item in transaksi.items.all():
                    try:
                        master_produk = Product.objects.get(sku=item.sku)
                        master_produk.stok_aktual += item.qty
                        master_produk.save()
                    except Product.DoesNotExist:
                        continue

            transaksi.delete()


            piutang_terhapus, _ = Piutang.objects.filter(nomor_invoice__iexact=str(nomor_invoice).strip()).delete()

            logger.info(
                f"Audit Log Master Delete: Invoice {nomor_invoice} dibersihkan. {piutang_terhapus} arsip piutang finance terhapus.")

            return Response(
                {"message": f"Transaksi {nomor_invoice} and seluruh lampiran piutang finance sukses dibersihkan."},
                status=status.HTTP_200_OK)

        except PosTransaction.DoesNotExist:
            return Response({"error": "Data transaksi tidak ditemukan di database server."},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Gagal melakukan master delete transaksi: %s", str(e), exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({"error": "Terjadi kesalahan internal pada server database."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({"error": "Terjadi kesalahan internal pada server database."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        alamat_pengiriman = request.data.get('alamat', 'Melalui Loket Kasir POS Proyek')

        jatuh_tempo_react = request.data.get('jatuh_tempo', request.data.get('jatuhTempo'))

        items_input = request.data.get('items', [])

        from admin_app.inventory.models import Product

        for item in items_input:
            sku_target = item.get('sku')
            qty_diminta = int(item.get('qty', 0))

            try:
                produk_gudang = Product.objects.get(sku=sku_target)

                if produk_gudang.stok_aktual < qty_diminta:
                    return Response(
                        {
                            "error": f"Transaksi Ditolak! Stok untuk produk '{produk_gudang.nama}' ({sku_target}) tidak mencukupi. Sisa stok berjalan: {produk_gudang.stok_aktual} Pcs."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Product.DoesNotExist:
                return Response(
                    {"error": f"Transaksi Ditolak! Produk dengan SKU {sku_target} tidak terdaftar di sistem gudang."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
                for item in items_input
            ]
        }

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("DETAIL EROR SERIALIZER PENJUALAN:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.perform_create(serializer)

            if data['metode_bayar'] == "TEMPO/KREDIT":
                try:
                    Piutang.objects.update_or_create(
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
                    logger.error("Gagal mencatat mutasi piutang otomatis pada ledger finance: %s", str(piutang_err))

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

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Length'] = str(len(pdf_bytes))
            response['Content-Disposition'] = f'attachment; filename="Invoice_{data["nomor_invoice"]}.pdf"'
            return response
        except Exception as e:
            logger.error("Gagal memproses transaksi kasir POS: %s", str(e), exc_info=True)
            return Response({"error": "Terjadi kesalahan internal pada server database."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==========================================================
    # SETTLE REKAP JUALAN MARKETPLACE
    # ==========================================================
    @action(detail=False, methods=['post'], url_path='settle-harian')
    @transaction.atomic
    def settle_harian_marketplace(self, request):
        data = request.data
        tanggal = data.get('tanggal', timezone.localdate())
        total_penjualan = data.get('total_penjualan', 0)
        items_input = data.get('items', [])

        if not items_input:
            return Response({"error": "Transaksi Ditolak! Paket data log item belanja harian kosong."},
                            status=status.HTTP_400_BAD_REQUEST)

        from admin_app.inventory.models import Product

        produk_tervalidasi = []
        for item in items_input:
            sku_target = item.get('sku')
            qty_diminta = int(item.get('qty', 0))

            try:
                produk_gudang = Product.objects.get(sku=sku_target)
                if produk_gudang.stok_aktual < qty_diminta:
                    return Response(
                        {
                            "error": f"Settle Gagal! Stok untuk '{produk_gudang.nama}' ({sku_target}) kurang. Sisa: {produk_gudang.stok_aktual} Pcs."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                produk_tervalidasi.append((produk_gudang, qty_diminta))
            except Product.DoesNotExist:
                return Response(
                    {"error": f"Settle Ditolak! SKU {sku_target} tidak terdaftar di database gudang."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            waktu_sekarang = timezone.now().strftime('%Y%m%d-%H%M%S')
            nomor_invoice_rekap = f"SETTLE-MP-{waktu_sekarang}"

            transaksi_rekap = PosTransaction.objects.create(
                nomor_invoice=nomor_invoice_rekap,
                pelanggan="REKAP MARKETPLACE ",
                alamat="Log Marketplace Harian PT Solution Corp",
                tanggal=tanggal,
                metode_bayar="TUNAI",
                status="Lunas",
                ongkir=0,
                grand_total=total_penjualan
            )

            from .models import PosTransactionItem
            for produk_obj, qty_potong in produk_tervalidasi:
                produk_obj.stok_aktual -= qty_potong
                produk_obj.save()

                item_data = next((i for i in items_input if i.get('sku') == produk_obj.sku), {})
                harga_jual = int(item_data.get('harga', 0))
                subtotal_harga = int(item_data.get('total', 0))

                PosTransactionItem.objects.create(
                    transaksi=transaksi_rekap,
                    sku=produk_obj.sku,
                    nama_produk=produk_obj.nama,
                    qty=qty_potong,
                    harga=harga_jual,
                    total=subtotal_harga
                )

            logger.info(f"Marketplace Settle Success: Invoice {nomor_invoice_rekap} dimasukkan ke jurnal sales.")

            return Response(
                {"message": "Settle harian sukses! Data berhasil disinkronkan ke laporan penjualan harian."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error("Gagal memproses master rekap settle marketplace: %s", str(e), exc_info=True)
            return Response({"error": f"Terjadi kesalahan internal pada server database: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==========================================================
    # DATA LIVE BREAKDOWN UNTUK PAPAN LABA RUGI
    # ==========================================================
    @action(detail=False, methods=['get'], url_path='laba-rugi-data')
    def laba_rugi_data(self, request):
        start_date_raw = request.query_params.get('start_date')
        end_date_raw = request.query_params.get('end_date')

        if not start_date_raw or not end_date_raw:
            hari_ini = timezone.localdate()
            start_date = hari_ini.replace(day=1)
            end_date = hari_ini
        else:
            try:
                start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Format tanggal wajib YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaksi_query = PosTransaction.objects.filter(tanggal__range=[start_date, end_date]).prefetch_related(
                'items')
            transactions_data = []

            from admin_app.inventory.models import Product

            for tx in transaksi_query:
                total_hpp_invoice = 0
                for item in tx.items.all():
                    try:
                        master_produk = Product.objects.get(sku__iexact=str(item.sku).strip())
                        harga_modal_satuan = master_produk.hpp if master_produk.hpp else 0
                        total_hpp_invoice += item.qty * harga_modal_satuan
                    except Product.DoesNotExist:
                        continue

                omset_bersih_murni = tx.grand_total - (getattr(tx, 'ongkir', 0) or 0)

                transactions_data.append({
                    "id": tx.id,
                    "nomor_invoice": tx.nomor_invoice,
                    "grand_total": omset_bersih_murni,
                    "total_hpp": total_hpp_invoice,
                    "tanggal": str(tx.tanggal)
                })

            return Response({
                "period": {"start": str(start_date), "end": str(end_date)},
                "transactions": transactions_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Gagal memproses breakdown laba rugi server: %s", str(e), exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
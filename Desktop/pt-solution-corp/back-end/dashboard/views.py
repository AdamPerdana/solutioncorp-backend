from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F
from datetime import datetime


from admin_app.sales.models import PosTransaction, PosTransactionItem
from admin_app.inventory.models import Product
from admin_app.finance.models import Biaya

class DashboardAnalyticsAPIView(APIView):
    def get(self, request, format=None):
        try:

            start_date_str = request.query_params.get('start_date', '2026-01-01')
            end_date_str = request.query_params.get('end_date', '2026-12-31')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()


            transaksi_qs = PosTransaction.objects.filter(
                tanggal__range=(start_date, end_date)
            ).prefetch_related('items')

            list_transaksi = []
            for tx in transaksi_qs:
                list_items = []
                for item in tx.items.all():
                    list_items.append({
                        "sku": item.sku,
                        "nama": item.nama_produk,
                        "qty": item.qty,
                        "total": int(item.total)
                    })

                list_transaksi.append({
                    "nomorInvoice": tx.nomor_invoice,
                    "pelanggan": tx.pelanggan,
                    "grand_total": int(tx.grand_total),
                    "ongkir": int(tx.ongkir if tx.ongkir else 0),
                    "items": list_items
                })


            master_hpp = {}
            produk_qs = Product.objects.all()
            for prod in produk_qs:
                master_hpp[prod.sku] = int(prod.hpp)
            biaya_qs = Biaya.objects.filter(tanggal__range=(start_date, end_date))
            list_biaya = []
            for b in biaya_qs:
                list_biaya.append({
                    "id": b.id,
                    "kategori": b.kategori,
                    "nominal": int(b.nominal)
                })

            tren_harian_qs = PosTransaction.objects.filter(
                tanggal__range=(start_date, end_date)
            ).values('tanggal').annotate(
                sales=Sum(F('grand_total') - F('ongkir'))
            ).order_by('tanggal')[:10]

            list_tren_harian = []
            for th in tren_harian_qs:
                if th['tanggal']:
                    list_tren_harian.append({
                        "tgl": th['tanggal'].strftime('%d/%m'),
                        "sales": int(th['sales'] if th['sales'] else 0)
                    })

            # 6. TREN BULANAN
            list_tren_bulanan = [
                {"bulan": "Jan", "sales": 18000000},
                {"bulan": "Feb", "sales": 22000000},
                {"bulan": "Jun", "sales": sum(th['sales'] for th in tren_harian_qs) if tren_harian_qs else 27985023},
                {"bulan": "Des", "sales": 40000000}
            ]

            data_response = {
                "transaksi": list_transaksi,
                "master_hpp": master_hpp,
                "catatan_biaya": list_biaya,
                "tren_harian": list_tren_harian,
                "tren_bulanan": list_tren_bulanan
            }

            return Response(data_response, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Internal Server Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
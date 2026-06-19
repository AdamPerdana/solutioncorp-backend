from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from .models import Piutang, Hutang, Biaya
from admin_app.inventory.models import PurchaseOrder, PurchaseOrderItem


class FinanceBackendComprehensiveTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hari_ini = timezone.now().date()

        # Setup base endpoints finance
        self.url_biaya = "/api/finance/biaya/"
        self.url_hutang = "/api/finance/hutang/"
        self.url_piutang = "/api/finance/piutang/"

    # ==========================================================
    #  [BIAYA OPERASIONAL]
    # ==========================================================
    def test_siklus_crud_biaya_operasional_dan_action_delete(self):
        payload_biaya = {
            "tanggal": str(self.hari_ini),
            "kategori": "Bensin & Transport",
            "metode": "Tunai / Kas Kecil",
            "nominal": 150000,
            "keterangan": "Bensin Pertalite Mobil Operasional Kurir"
        }
        res_post = self.client.post(self.url_biaya, payload_biaya, format='json')
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Biaya.objects.count(), 1)

        biaya_id = res_post.data['id']
        res_delete = self.client.delete(f"{self.url_biaya}{biaya_id}/")


        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Biaya.objects.count(), 0)

    # ==========================================================
    #  [HUTANG & CROSS-APP COUPLING]
    # ==========================================================
    def test_retrieve_detail_hutang_and_cross_app_query_manifes_barang(self):
        po_gudang = PurchaseOrder.objects.create(
            nomor_po="PO/2026/06/999",
            supplier="Pxton Factory",
            tanggal=self.hari_ini,
            grand_total=500000
        )
        PurchaseOrderItem.objects.create(
            purchase_order=po_gudang,
            sku="STR-01",
            nama_produk="Sterno Kaleng Original",
            qty=100,
            harga_beli=5000,
            total=500000
        )

        hutang_record = Hutang.objects.create(
            nomor_po=" po/2026/06/999 ",
            supplier="Pxton Factory",
            tanggal_po=self.hari_ini,
            deskripsi_barang="100 Pcs Sterno Kaleng Original",
            total_tagihan=500000,
            sisa_hutang=500000,
            status_hutang="Belum Lunas"
        )

        res_get = self.client.get(f"{self.url_hutang}{hutang_record.id}/")

        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertIn('items', res_get.data)
        self.assertEqual(len(res_get.data['items']), 1)
        self.assertEqual(res_get.data['items'][0]['sku'], "STR-01")

    def test_partial_update_patch_status_keuangan_hutang(self):
        hutang_test = Hutang.objects.create(
            nomor_po="PO-MUTASI-01",
            supplier="Vendor Gel Indonesia",
            tanggal_po=self.hari_ini,
            total_tagihan=1000000,
            sisa_hutang=1000000,
            status_hutang="Belum Lunas"
        )

        payload_patch = {
            "status_hutang": "Lunas",
            "sisa_hutang": 0
        }
        res_patch = self.client.patch(f"{self.url_hutang}{hutang_test.id}/", payload_patch, format='json')

        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)

        hutang_test.refresh_from_db()
        self.assertEqual(hutang_test.status_hutang, "Lunas")
        self.assertEqual(hutang_test.sisa_hutang, 0)

    # ==========================================================
    # [PIUTANG DAGANG]
    # ==========================================================
    def test_retrieve_detail_piutang_returns_fallback_if_pos_not_found(self):
        piutang_test = Piutang.objects.create(
            nomor_invoice="INV-GAIB-404",
            pelanggan="Toko Resto Bassura",
            tanggal_transaksi=self.hari_ini,
            jatuh_tempo=self.hari_ini + timedelta(days=14),
            total_tagihan=300000,
            sisa_piutang=300000,
            status_piutang="Belum Lunas"
        )

        res_get = self.client.get(f"{self.url_piutang}{piutang_test.id}/")

        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['items'], [])
        self.assertEqual(res_get.data['alamat'], "Jakarta")
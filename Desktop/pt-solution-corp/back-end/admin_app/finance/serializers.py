from rest_framework import serializers
from .models import Piutang

# ==========================================================
# [SERIALIZER PIUTANG ]
# ==========================================================
class PiutangSerializer(serializers.ModelSerializer):
    class Meta:
        model = Piutang
        # Memetakan seluruh parameter data piutang
        fields = [
            'id', 'nomor_invoice', 'pelanggan', 'tanggal_transaksi',
            'jatuh_tempo', 'total_tagihan', 'sisa_piutang', 'status_piutang'
        ]
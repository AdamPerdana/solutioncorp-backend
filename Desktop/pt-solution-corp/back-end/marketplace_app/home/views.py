from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from marketplace_app.product.models import Product
from .serializers import HomeProductSerializer

#  1. KONTROLLER UNTUK HALAMAN UTAMA (KATALOG 3 PRODUK)
class HomeProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = HomeProductSerializer
    permission_classes = [AllowAny]  # Publik agar pembeli bisa lihat katalog tanpa login


# 2. KONTROLLER UNTUK HALAMAN DETAIL PRODUK (BERDASARKAN SLUG)
class HomeProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = HomeProductSerializer
    permission_classes = [AllowAny]  # Publik agar pembeli bisa lihat detail tanpa login
    lookup_field = 'slug'            # Mencari data menggunakan teks slug nama produk
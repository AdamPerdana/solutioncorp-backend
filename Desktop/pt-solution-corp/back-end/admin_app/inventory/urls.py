from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet,SupplierViewSet,PurchaseOrderViewSet


router = DefaultRouter()
#PRODUK
router.register(r'products', ProductViewSet, basename='product')
#SUPPLIER
router.register(r'suppliers', SupplierViewSet, basename='supplier')
#PURCHASE ORDER(PO)
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')


urlpatterns = [
    path('', include(router.urls)),
]
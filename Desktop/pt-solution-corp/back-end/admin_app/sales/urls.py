from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet,ProformaInvoiceViewSet,PosTransactionViewSet

router = DefaultRouter()
router.register('customers', CustomerViewSet)
router.register(r'proforma-invoices', ProformaInvoiceViewSet, basename='proforma-invoice')
router.register(r'pos-transactions', PosTransactionViewSet, basename='pos-transactions')

urlpatterns = [
    path('', include(router.urls)),
]


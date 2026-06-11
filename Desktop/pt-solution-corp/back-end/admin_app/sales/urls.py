from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet,ProformaInvoiceViewSet

router = DefaultRouter()
router.register('customers', CustomerViewSet)
router.register(r'proforma-invoices', ProformaInvoiceViewSet, basename='proforma-invoice')

urlpatterns = [
    path('', include(router.urls)),
]
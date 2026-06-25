from django.urls import path
from .views import CheckoutLeadsCreateView

urlpatterns = [
    # Cukup ketik 'submit/' saja
    path('submit/', CheckoutLeadsCreateView.as_view(), name='checkout-submit'),
]
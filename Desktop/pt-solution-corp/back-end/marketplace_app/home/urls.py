from django.urls import path
from marketplace_app.home.views import HomeProductListView,HomeProductDetailView

urlpatterns = [
    path('products/', HomeProductListView.as_view(), name='home-products'),
    path('products/<slug:slug>/', HomeProductDetailView.as_view(), name='home-product-detail'),
]
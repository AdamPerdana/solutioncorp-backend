from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PiutangViewSet

router = DefaultRouter()
router.register(r'piutang', PiutangViewSet, basename='piutang')

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PiutangViewSet,HutangViewSet, BiayaViewSet

router = DefaultRouter()
router.register(r'piutang', PiutangViewSet, basename='piutang')
router.register(r'hutang', HutangViewSet, basename='finance-hutang')
router.register(r'biaya', BiayaViewSet, basename='biaya')

urlpatterns = [
    path('', include(router.urls)),
]
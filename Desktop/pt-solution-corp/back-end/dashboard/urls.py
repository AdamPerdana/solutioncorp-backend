from django.urls import path
from .views import DashboardAnalyticsAPIView

urlpatterns = [
    path('dashboard/', DashboardAnalyticsAPIView.as_view(), name='dashboard_analytics'),
]
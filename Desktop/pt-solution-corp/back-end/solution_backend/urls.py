from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static     

urlpatterns = [
    path("admin/", admin.site.urls),
    #SALES
    path('api/sales/', include('admin_app.sales.urls')),
    #INVENTORY
    path('api/inventory/', include('admin_app.inventory.urls')),
    # FINANCE
    path('api/finance/', include('admin_app.finance.urls')),
    #Dashboard
    path('api/', include('dashboard.urls')),

    #TOKEN
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),

    #MARKETPLACE
    path('api/home/', include('marketplace_app.home.urls')),
    path('api/checkout/', include('marketplace_app.checkout.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
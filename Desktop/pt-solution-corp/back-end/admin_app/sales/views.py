from rest_framework import viewsets
from .models import Customer
from .serializers import CustomerSerializer

#Customer
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('id')
    serializer_class = CustomerSerializer

# Create your views here.

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .serializers import CheckoutSerializer


class CheckoutLeadsCreateView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = CheckoutSerializer
    permission_classes = [AllowAny]  #


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "message": "Data leads pemesanan berhasil disimpan.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Data tidak valid atau terdeteksi karakter berbahaya!",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
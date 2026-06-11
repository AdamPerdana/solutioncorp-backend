import json
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response

from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page

from .models import Customer, ProformaInvoice
from .serializers import CustomerSerializer, ProformaInvoiceSerializer
from .utility import generate_proforma_pdf_output


#CUSTOMER
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('id')
    serializer_class = CustomerSerializer


# PROFORMA INVOICE
@method_decorator(gzip_page, name='dispatch')
class ProformaInvoiceViewSet(viewsets.ModelViewSet):
    queryset = ProformaInvoice.objects.all()
    serializer_class = ProformaInvoiceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice_data = serializer.validated_data
            items_data = request.data.get('items', [])

            pdf_raw_string = generate_proforma_pdf_output(invoice_data, items_data)
            pdf_bytes = pdf_raw_string.encode('latin-1')

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Length'] = str(len(pdf_bytes))
            response['Content-Disposition'] = f'attachment; filename="Proforma_{request.data.get("nomor_invoice")}.pdf"'

            return response

        except Exception as e:
            return Response(
                {"error": f"Gagal memproses dokumen PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
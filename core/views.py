import calendar

from rest_framework import viewsets, mixins, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Shareholder, Share, Payment
from .serializers import (
    ShareholderModelSerializer, ShareModelSerializer, PaymentModelSerializer,
    ShareSerializer, ShareSummarySerializer, InstallmentDueDetailsSerializer
)


class ShareholderViewSet(viewsets.ModelViewSet):
    queryset = Shareholder.objects.all()
    serializer_class = ShareholderModelSerializer
    http_method_names = ["list", "get", "post", "delete"]
    # permission_classes = [IsAuthenticated]


class ShareListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Share.objects.all()
    serializer_class = ShareModelSerializer
    # permission_classes = [IsAuthenticated]


class ShareModelViewSet(viewsets.ModelViewSet):
    queryset = Share.objects.all()
    serializer_class = ShareSerializer
    # permission_classes = [IsAuthenticated]

    def create(self, request):
        # Validate and create a new Share instance
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentModelViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentModelSerializer
    # permission_classes = [IsAuthenticated]


class ShareSummaryAndDetailsView(views.APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        month = request.query_params.get('month', None)
        year = request.query_params.get('year', None)

        # Filter shares and payments based on month and year
        shares = Share.objects.all()
        payments = Payment.objects.all()
        if month is not None:
            if not month.isdigit() or not 1 <= int(month) <= 12:
                return Response({'message': 'Wrong input'}, status=status.HTTP_400_BAD_REQUEST)
            shares = shares.filter(start_date__month=month)
            payments = payments.filter(due_date__month=month)
            month = calendar.month_name[month]
        if year is not None:
            shares = shares.filter(start_date__year=year)
            payments = payments.filter(due_date__year=year)

        # Calculate and serialize summary data
        total_collected = sum(p.amount for p in payments)
        total_expected = sum(s.annual_amount for s in shares)
        due_amount = sum(s.annual_amount - p.amount for s, p in zip(shares, payments))

        summary_data = ShareSummarySerializer({
            "month": month or "",
            "year": year or "",
            "total_collected": total_collected,
            "total_expected": total_expected,
            "due_amount": due_amount,
        }).data

        # Serialize and return installment details
        details_data = InstallmentDueDetailsSerializer(payments, many=True).data

        # Combine and return data
        return Response({
            "summary": summary_data,
            "details": details_data,
        })

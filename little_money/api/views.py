from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from payment.models import PlatformSettings, Transaction
from payment.services import PaymentAggregatorClient
from django.utils.crypto import get_random_string
from rest_framework import generics
from rest_framework import serializers

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_transaction(request):
    base_amount = float(request.data.get("amount"))

    settings_obj = PlatformSettings.objects.first()
    if not settings_obj:
        platform_fee_percent = 1.00
    else:
        platform_fee_percent = float(settings_obj.platform_fee_percent)

    platform_fee_amount = base_amount * (platform_fee_percent / 100)
    total_amount = base_amount + platform_fee_amount

    transaction_id = get_random_string(12)

    txn = Transaction.objects.create(
        user=request.user,
        transaction_id=transaction_id,
        base_amount=base_amount,
        platform_fee_percent=platform_fee_percent,
        platform_fee_amount=platform_fee_amount,
        total_amount=total_amount
    )

    client = PaymentAggregatorClient()
    result = client.initiate_payment({
        "transaction_id": transaction_id,
        "amount": total_amount
    })

    return Response({
        "transaction": txn.transaction_id,
        "base_amount": base_amount,
        "platform_fee_percent": platform_fee_percent,
        "platform_fee_amount": platform_fee_amount,
        "total_amount_sent_to_aggregator": total_amount,
        "aggregator_response": result
    })

class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


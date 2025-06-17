from rest_framework.decorators import api_view
from rest_framework.response import Response
from payment.models import Transaction
from payment.services import PaymentAggregatorClient

@api_view(['POST'])
def webhook_handler(request):
    txn_id = request.data.get('transaction_id')
    status = request.data.get('status')

    txn = Transaction.objects.filter(transaction_id=txn_id).first()
    if txn:
        txn.status = status
        txn.save()
        client = PaymentAggregatorClient()
        client.notify_user(txn.user.email, status)

    return Response({"message": "Webhook processed"}, status=200)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction
from .serializers import TransactionSerializer
from reports.models import WasteReport

COINS_PER_REDEEM = 100
INR_PER_REDEEM = 10  # ₹10 per 100 coins

class RewardsSummaryView(APIView):
    def get(self, request):
        user = request.user
        total_reports = WasteReport.objects.filter(reported_by=user).count()
        total_collected = WasteReport.objects.filter(reported_by=user, status='collected').count()
        return Response({
            'coins': user.coins,
            'total_reports': total_reports,
            'total_collected': total_collected,
            'environmental_index': (total_collected / total_reports * 100) if total_reports > 0 else 0
        })

class TransactionListView(APIView):
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class RedeemCoinsView(APIView):
    def post(self, request):
        user = request.user
        # Support variable amount from request, default to 100
        try:
            amount = int(request.data.get('amount', 100))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

        if amount < 100:
            return Response({'error': 'Minimum redemption amount is 100 coins.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.coins < amount:
            return Response(
                {'error': f'Insufficient coins. You have {user.coins} coins.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate INR value (₹10 per 100 coins)
        inr_value = (amount * 0.10)

        # Deduct coins and record transaction (Signal will handle balance deduction)
        method = request.data.get('method', 'UPI')
        details = request.data.get('details', '')
        
        Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='redeemed',
            description=f'Redeemed {amount} coins via {method} ({details}) for \u20b9{inr_value:.2f}'
        )


        return Response({
            'success': True,
            'message': f'Successfully redeemed {amount} coins for \u20b9{inr_value:.2f}!',
            'coins_deducted': amount,
            'inr_credited': inr_value,
            'remaining_coins': user.coins
        }, status=status.HTTP_200_OK)

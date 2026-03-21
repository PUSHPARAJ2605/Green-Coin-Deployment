from django.urls import path
from .views import RewardsSummaryView, TransactionListView, RedeemCoinsView

urlpatterns = [
    path('summary/', RewardsSummaryView.as_view(), name='rewards-summary'),
    path('transactions/', TransactionListView.as_view(), name='transactions-list'),
    path('redeem/', RedeemCoinsView.as_view(), name='rewards-redeem'),
]

from rewards.models import Transaction
from accounts.models import CustomUser
from django.db.models import Sum

# 1. Clean up crazy high transactions
print("Cleaning up corrupted transactions...")
corrupted_txs = Transaction.objects.filter(amount__gt=1000000)
for tx in corrupted_txs:
    print(f"Deleting corrupted TX: {tx.transaction_type} of {tx.amount} for {tx.user.email}")
    tx.delete()

# 2. Recalculate ALL user balances from their transaction history
print("\nRecalculating all user balances...")
for user in CustomUser.objects.all():
    earned = Transaction.objects.filter(user=user, transaction_type='earned').aggregate(Sum('amount'))['amount__sum'] or 0
    redeemed = Transaction.objects.filter(user=user, transaction_type='redeemed').aggregate(Sum('amount'))['amount__sum'] or 0
    penalty = Transaction.objects.filter(user=user, transaction_type='penalty').aggregate(Sum('amount'))['amount__sum'] or 0
    
    new_balance = max(0, earned - redeemed - penalty)
    old_balance = user.coins
    
    if old_balance != new_balance:
        user.coins = new_balance
        user.save()
        print(f"Updated {user.email}: {old_balance} -> {new_balance} (E:{earned}, R:{redeemed}, P:{penalty})")
    else:
        print(f"User {user.email} already in sync ({new_balance} coins).")

print("\nCleanup and sync complete.")

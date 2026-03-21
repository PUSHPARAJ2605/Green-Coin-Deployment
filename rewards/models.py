from django.db import models
from accounts.models import CustomUser

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('earned', 'Earned'),
        ('redeemed', 'Redeemed'),
        ('penalty', 'Penalty'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F

@receiver(post_save, sender=Transaction)
def update_user_balance(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        if instance.transaction_type == 'earned':
            CustomUser.objects.filter(id=user.id).update(coins=F('coins') + instance.amount)
        elif instance.transaction_type in ['redeemed', 'penalty']:
            CustomUser.objects.filter(id=user.id).update(coins=F('coins') - instance.amount)
        
        # Refresh user from db to get exact updated coins
        user.refresh_from_db()
        
        # Broadcast the balance update to connected clients
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "waste_updates",
            {
                "type": "status_update",
                "message": "transaction_created",
                "user_id": user.id,
                "new_balance": user.coins
            }
        )

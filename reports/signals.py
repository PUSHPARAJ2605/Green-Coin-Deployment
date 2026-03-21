from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import WasteReport

@receiver(post_save, sender=WasteReport)
def report_status_update(sender, instance, created, **kwargs):
    if not created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "waste_updates",
            {
                "type": "status_update",
                "report_id": instance.id,
                "status": instance.status,
                "collector_name": instance.collected_by.full_name if instance.collected_by else "N/A",
                "coins": instance.coins_awarded
            }
        )

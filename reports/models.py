from django.db import models
from accounts.models import CustomUser

class WasteReport(models.Model):
    WASTE_TYPE_CHOICES = (
        ('Garbage on Road', 'Garbage on Road'),
        ('Plastic Waste', 'Plastic Waste'),
        ('Construction Waste', 'Construction Waste'),
        ('Medical Waste', 'Medical Waste'),
        ('Other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('picking', 'Picking'),
        ('collected', 'Collected'),
    )
    reported_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    waste_type = models.CharField(max_length=50, choices=WASTE_TYPE_CHOICES)
    description = models.TextField()
    photo = models.ImageField(upload_to='reports/', max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    coins_awarded = models.IntegerField(default=10)
    reported_at = models.DateTimeField(auto_now_add=True)
    collected_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickups')
    collected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Report #{self.id} - {self.status}"

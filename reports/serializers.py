from rest_framework import serializers
from .models import WasteReport

class WasteReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.ReadOnlyField(source='reported_by.full_name')
    collected_by_name = serializers.ReadOnlyField(source='collected_by.full_name')

    class Meta:
        model = WasteReport
        fields = '__all__'
        read_only_fields = ('reported_by', 'collected_by', 'collected_at', 'coins_awarded')

from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.db.models import F
from .models import WasteReport

from .serializers import WasteReportSerializer
from rewards.models import Transaction
import imagehash
from PIL import Image
import io

class WasteReportViewSet(viewsets.ModelViewSet):
    queryset = WasteReport.objects.all()
    serializer_class = WasteReportSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        if self.action == 'list':
            return WasteReport.objects.filter(status__in=['pending', 'picking', 'collected'])
        return super().get_queryset()

    def perform_create(self, serializer):
        photo = self.request.FILES.get('photo')
        waste_type = self.request.data.get('waste_type')
        
        # Calculate coins based on waste type
        reward_map = {
            'Garbage on Road': 10,
            'Plastic Waste': 15,
            'Construction Waste': 20,
            'Medical Waste': 30,
            'Other': 0  # To be decided by collector
        }
        coins = reward_map.get(waste_type, 10)

        if photo:
            img = Image.open(photo)
            h = str(imagehash.average_hash(img))
            
            # Check for duplicate hash
            is_duplicate = WasteReport.objects.filter(description__icontains=h).exists()
            
            # Enhanced "AI" Validation
            is_spam = False
            filename_lower = photo.name.lower()
            
            # 1. Filename checks
            if any(word in filename_lower for word in ['spam', 'screenshot', 'test', 'dummy', 'wallpaper', 'background']):
                is_spam = True
                
            # 2. Image contents analysis (differentiate clipart/borders from real photos)
            try:
                # We already loaded 'img' above
                img_rgb = img.convert('RGB')
                w, h = img_rgb.size
                
                # Reject extreme aspect ratios (banners, dividers, sidebars)
                if w / h > 2.5 or h / w > 2.5:
                    is_spam = True
                
                # Reject low color variance (clipart, solid colors)
                # Resize to analyze color distribution efficiently
                small_img = img_rgb.resize((100, 100))
                
                # Pillow < 14 uses getdata(), newer uses get_flattened_data() or similar.
                # getcolors() returns a list of (count, pixel) or None if > maxcolors.
                colors = small_img.getcolors(maxcolors=10000)
                if colors is not None:
                    # If it successfully fit into 10,000 unique colors, it might be clipart.
                    # 100x100 = 10,000 pixels. Real photos typically have > 8,000 colors, 
                    # but definitely > 5,000 unless it's a completely black frame.
                    unique_colors = len(colors)
                    if unique_colors < 5000:
                        is_spam = True
            except Exception as e:
                print(f"Image analysis error: {e}")
                pass
            if is_duplicate or is_spam:
                Transaction.objects.create(
                    user=self.request.user,
                    amount=20,
                    transaction_type='penalty',
                    description="Penalty for invalid/duplicate report image"
                )
                if is_duplicate:
                    raise serializers.ValidationError("Duplicate image detected! You have been penalized 20 coins.")
                else:
                    raise serializers.ValidationError("AI strictly rejected this image. You have been penalized 20 coins.")

            # Save the hash in the description so we can find it next time
            desc = serializer.validated_data.get('description', '')
            desc = f"{desc}\n[HASH:{h}]"
            serializer.save(reported_by=self.request.user, coins_awarded=coins, description=desc)
        else:
            serializer.save(reported_by=self.request.user, coins_awarded=coins)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        reports = WasteReport.objects.filter(reported_by=request.user)
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        report = self.get_object()
        new_status = request.data.get('status')
        
        if new_status == 'picking':
            report.status = 'picking'
            report.collected_by = request.user
            report.save()
        elif new_status == 'collected':
            report.status = 'collected'
            report.collected_at = timezone.now()
            report.save()
            
            # Award coins to the reporter
            reporter = report.reported_by
            if report.waste_type == 'Other':
                # Collector must decide coins for 'Other' type
                custom_coins = int(request.data.get('coins', 0))
                report.coins_awarded = custom_coins
                report.save()

            # Create transaction record (Signal will handle balance update)
            Transaction.objects.create(

                user=reporter,
                amount=report.coins_awarded,
                transaction_type='earned',
                description=f"Earned from report #{report.id} ({report.waste_type})"
            )
            
            # Signal will handle WebSocket broadcast
            
        return Response(WasteReportSerializer(report).data)

class CollectorActivePickupsView(viewsets.ViewSet):
    def list(self, request):
        pickups = WasteReport.objects.filter(collected_by=request.user, status='picking')
        serializer = WasteReportSerializer(pickups, many=True)
        return Response(serializer.data)

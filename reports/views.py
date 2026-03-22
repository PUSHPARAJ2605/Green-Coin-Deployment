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
            'Dead Animals': 50,  # High reward for specialized disposal
            'Other': 0  # To be decided by collector
        }
        coins = reward_map.get(waste_type, 10)

        if photo:
            img = Image.open(photo)
            h = str(imagehash.average_hash(img))
            
            # Check for duplicate hash
            is_duplicate = WasteReport.objects.filter(description__icontains=h).exists()
            
            # Enhanced AI Validation Logic
            is_spam = False
            filename_lower = photo.name.lower()
            
            # 1. Filename checks (Expanded)
            spam_keywords = ['spam', 'screenshot', 'test', 'dummy', 'wallpaper', 'background', 'logo', 'icon']
            if any(word in filename_lower for word in spam_keywords):
                is_spam = True
                
            # 2. Image contents analysis (Detailed Variance Check)
            try:
                img_rgb = img.convert('RGB')
                w, h_img = img_rgb.size
                
                # Reject extreme aspect ratios (non-camera formats)
                if w / h_img > 3.0 or h_img / w > 3.0:
                    is_spam = True
                
                # Analyze color distribution
                small_img = img_rgb.resize((100, 100))
                colors = small_img.getcolors(maxcolors=10000)
                
                if colors is not None:
                    unique_colors = len(colors)
                    # Real photos of waste/animals have high color diversity (>3000 unique colors in 100x100)
                    # Simple clipart or solid backgrounds usually have <1500 colors.
                    if unique_colors < 2000:
                        is_spam = True
            except Exception as e:
                print(f"AI Analysis Error: {e}")
                pass

            if is_duplicate or is_spam:
                Transaction.objects.create(
                    user=self.request.user,
                    amount=20,
                    transaction_type='penalty',
                    description=f"Penalty: {'Duplicate' if is_duplicate else 'AI rejected invalid'} image upload"
                )
                if is_duplicate:
                    raise serializers.ValidationError("Duplicate image detected! You have been penalized 20 coins.")
                else:
                    raise serializers.ValidationError("AI Analysis: This image looks like clipart or a screenshot. Please upload a real photo. (20 coins penalized)")

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

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
        try:
            photo = self.request.FILES.get('photo')
            waste_type = self.request.data.get('waste_type')
            
            reward_map = {
                'Garbage on Road': 10,
                'Plastic Waste': 15,
                'Construction Waste': 20,
                'Medical Waste': 30,
                'Dead Animals': 50,
                'Other': 0
            }
            coins = reward_map.get(waste_type, 10)

            if photo:
                try:
                    img = Image.open(photo)
                    img.verify()
                    img = Image.open(photo)
                    
                    h = str(imagehash.average_hash(img))
                    is_duplicate = WasteReport.objects.filter(description__icontains=h).exists()
                    
                    is_spam = False
                    filename_lower = photo.name.lower()
                    
                    spam_keywords = ['spam', 'screenshot', 'test', 'dummy', 'wallpaper', 'background', 'logo', 'icon']
                    if any(word in filename_lower for word in spam_keywords):
                        is_spam = True
                        
                    try:
                        img_rgb = img.convert('RGB')
                        w, h_img = img_rgb.size
                        if w / h_img > 3.0 or h_img / w > 3.0:
                            is_spam = True
                        
                        small_img = img_rgb.resize((100, 100))
                        colors = small_img.getcolors(maxcolors=10000)
                        if colors is not None and len(colors) < 1500:
                            is_spam = True
                    except:
                        pass

                    if is_duplicate or is_spam:
                        Transaction.objects.create(
                            user=self.request.user,
                            amount=20,
                            transaction_type='penalty',
                            description=f"Penalty: {'Duplicate' if is_duplicate else 'AI rejected invalid'} image upload"
                        )
                        if is_duplicate:
                            raise serializers.ValidationError({"error": "Duplicate image detected! You have been penalized 20 coins."})
                        else:
                            raise serializers.ValidationError({"error": "AI Analysis: This image looks like clipart or a screenshot. 20 coins penalized."})

                    desc = serializer.validated_data.get('description', '')
                    desc = f"{desc}\n[HASH:{h}]"
                    serializer.save(reported_by=self.request.user, coins_awarded=coins, description=desc)
                except serializers.ValidationError:
                    raise
                except Exception as e:
                    print(f"Image processing fallback: {e}")
                    serializer.save(reported_by=self.request.user, coins_awarded=coins)
            else:
                serializer.save(reported_by=self.request.user, coins_awarded=coins)
        except serializers.ValidationError:
            raise
        except Exception as e:
            # Final safety net: Return the actual error message to the frontend for debugging
            raise serializers.ValidationError({"error": f"Server Error: {str(e)}"})

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

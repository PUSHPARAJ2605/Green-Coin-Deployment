from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WasteReportViewSet, CollectorActivePickupsView

router = DefaultRouter()
router.register(r'', WasteReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('mine/', WasteReportViewSet.as_view({'get': 'mine'}), name='reports-mine'),
    path('collector/active/', CollectorActivePickupsView.as_view({'get': 'list'}), name='collector-active'),
]

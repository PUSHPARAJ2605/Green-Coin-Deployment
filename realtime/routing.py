from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/reports/', consumers.WasteConsumer.as_asgi()),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, ProxyAPIView, ThingsboardDevicesAPIView, thingsboard_device_telemetry

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')

urlpatterns = [
    path('', include(router.urls)),
    # Proxy path: everything after `wrapper/proxy/` is forwarded to ThingsBoard
    path('wrapper/proxy/<path:path>', ProxyAPIView.as_view(), name='thingsboard-proxy'),
    # ThingsBoard wrapper endpoints
    path('wrapper/devices/', ThingsboardDevicesAPIView.as_view(), name='thingsboard-devices'),
    path('wrapper/devices/<str:device_id>/telemetry/latest/', thingsboard_device_telemetry, name='thingsboard-device-telemetry'),
]

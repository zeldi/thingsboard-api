from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
from .models import Device
from .serializers import DeviceSerializer
from .thingsboard import proxy_request, get_tenant_devices, get_device_latest_telemetry


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('-created_at')
    serializer_class = DeviceSerializer


class ProxyAPIView(APIView):
    """Proxy any request under `wrapper/proxy/<path:path>` to the configured ThingsBoard URL.

    The path captured is appended to the ThingsBoard base URL. Authorization header
    from `THINGSBOARD_API_TOKEN` (if set) will be included automatically.
    """

    def dispatch(self, request, path=None, *args, **kwargs):
        try:
            resp = proxy_request(request, path)
        except RuntimeError as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Build DRF Response from proxied response
        content_type = resp.headers.get('Content-Type', 'application/json')
        try:
            data = resp.json()
        except Exception:
            data = resp.text

        # Return response with proxied status code
        return Response(data, status=resp.status_code, headers={k: v for k, v in resp.headers.items() if k.lower() != 'transfer-encoding'})


class ThingsboardDevicesAPIView(APIView):
    """List all tenant devices from ThingsBoard."""

    def get(self, request):
        try:
            page_size = int(request.query_params.get('pageSize', 100))
            page = int(request.query_params.get('page', 0))
            devices, total = get_tenant_devices(page_size=page_size, page=page)
            return Response({
                'data': devices,
                'totalElements': total,
                'pageSize': page_size,
                'page': page,
            })
        except requests.RequestException as e:
            return Response({'detail': f'ThingsBoard error: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def thingsboard_device_telemetry(request, device_id):
    """Get latest telemetry values for a specific device."""
    try:
        keys = request.query_params.get('keys', None)  # optional: 'temp,humidity'
        latest = get_device_latest_telemetry(device_id, keys=keys)
        return Response({'device_id': device_id, 'latest_telemetry': latest})
    except requests.RequestException as e:
        return Response({'detail': f'ThingsBoard error: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

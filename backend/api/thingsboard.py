import requests
from django.conf import settings


def build_tb_url(path: str) -> str:
    """Build the full URL to ThingsBoard for a given path.

    `path` should not start with a leading '/'. Example: 'api/tenant/devices'.
    """
    base = settings.THINGSBOARD_URL.rstrip('/') if settings.THINGSBOARD_URL else ''
    if not base:
        raise RuntimeError('THINGSBOARD_URL is not configured')
    return f"{base}/{path.lstrip('/')}"


def proxy_request(django_request, path: str):
    """Proxy the incoming Django request to ThingsBoard and return requests.Response.

    This forwards method, query params, headers (filtered), and body. It injects
    Authorization header from `THINGSBOARD_API_TOKEN` if provided in settings.
    """
    method = django_request.method.lower()
    url = build_tb_url(path)

    # Forward query params
    params = django_request.GET.dict()

    # Headers - forward minimal set and exclude host-related headers
    headers = {}
    for k, v in django_request.headers.items():
        # Skip headers that shouldn't be proxied
        if k.lower() in ('host', 'content-length', 'connection'):
            continue
        headers[k] = v

    # Add ThingsBoard API token if configured
    if settings.THINGSBOARD_API_TOKEN:
        headers['Authorization'] = f"Bearer {settings.THINGSBOARD_API_TOKEN}"

    data = None
    json = None
    content_type = django_request.content_type or ''
    if content_type.startswith('application/json'):
        try:
            json = django_request.data if hasattr(django_request, 'data') else django_request.body
        except Exception:
            json = None
    else:
        data = django_request.body or None

    # Use requests to perform the proxied call
    request_func = getattr(requests, method, None)
    if not request_func:
        raise RuntimeError(f'HTTP method not supported: {django_request.method}')

    resp = request_func(url, params=params, headers=headers, data=data if data else None, json=json if json else None, timeout=30)
    return resp


def get_tenant_devices(page_size: int = 100, page: int = 0):
    """Fetch tenant devices from ThingsBoard.
    
    Returns a tuple: (list of devices, total count, or exception).
    """
    headers = {}
    if settings.THINGSBOARD_API_TOKEN:
        headers['Authorization'] = f"Bearer {settings.THINGSBOARD_API_TOKEN}"
    
    url = build_tb_url('api/tenant/devices')
    params = {'pageSize': page_size, 'page': page, 'sortProperty': 'createdTime', 'sortOrder': 'DESC'}
    
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    # ThingsBoard returns { data: [...], totalElements: N, ... }
    devices = data.get('data', [])
    total = data.get('totalElements', 0)
    return devices, total


def get_device_latest_telemetry(device_id: str, keys: str = None):
    """Fetch latest telemetry values for a device.
    
    `keys` is an optional comma-separated list of telemetry keys. If not provided,
    all keys are fetched.
    
    Returns a dict: { key: { value: val, timestamp: ts }, ... } for the latest values with timestamps.
    """
    headers = {}
    if settings.THINGSBOARD_API_TOKEN:
        headers['Authorization'] = f"Bearer {settings.THINGSBOARD_API_TOKEN}"
    
    url = build_tb_url(f'api/plugins/telemetry/DEVICE/{device_id}/values/timeseries')
    params = {}
    if keys:
        params['keys'] = keys
    
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    # ThingsBoard returns { key: [{ ts: timestamp, value: val }, ...], ... }
    # Extract only the latest value and timestamp for each key
    latest = {}
    for key, values in data.items():
        if isinstance(values, list) and len(values) > 0:
            latest_entry = values[-1]  # last entry is most recent
            latest[key] = {
                'value': latest_entry['value'],
                'timestamp': latest_entry['ts']
            }
    return latest

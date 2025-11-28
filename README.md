# thingsboard-api

## Django backend (quickstart)

This repository contains a Django REST backend with a wrapper API for ThingsBoard IoT platform under `backend/`.

### Setup

- Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Run migrations and start the development server:

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

- The API root will be available at `http://127.0.0.1:8000/api/`.

### Configuration

Set environment variables to connect to ThingsBoard:

```bash
export THINGSBOARD_URL='https://demo.thingsboard.io'
export THINGSBOARD_API_TOKEN='your_api_token_here'  # optional
```

### ThingsBoard Wrapper Endpoints

#### 1. List all tenant devices
**GET** `/api/wrapper/devices/`

Query parameters (optional):
- `pageSize`: number of devices per page (default: 100)
- `page`: page number (default: 0)

Example:
```bash
curl http://127.0.0.1:8000/api/wrapper/devices/?pageSize=50
```

Response:
```json
{
  "data": [
    {
      "id": { "id": "device-uuid" },
      "createdTime": 1234567890000,
      "name": "Temperature Sensor",
      "type": "default",
      "customerId": { "id": "customer-uuid" },
      ...
    }
  ],
  "totalElements": 42,
  "pageSize": 50,
  "page": 0
}
```

#### 2. Get latest telemetry for a device
**GET** `/api/wrapper/devices/{deviceId}/telemetry/latest/`

Query parameters (optional):
- `keys`: comma-separated telemetry keys (e.g., `temp,humidity`). If not provided, all keys are fetched.

Example:
```bash
curl "http://127.0.0.1:8000/api/wrapper/devices/123e4567-e89b-12d3-a456-426614174000/telemetry/latest/?keys=temperature,humidity"
```

Response:
```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "latest_telemetry": {
    "temperature": 23.5,
    "humidity": 65.2
  }
}
```

#### 3. Generic proxy (for other ThingsBoard endpoints)
**ANY** `/api/wrapper/proxy/<path>`

Use this to proxy any ThingsBoard API call. All query params, headers, and body are forwarded, and the `THINGSBOARD_API_TOKEN` is injected if configured.

Example:
```bash
curl http://127.0.0.1:8000/api/wrapper/proxy/api/tenant/devices
```

### Notes

- This is a development scaffold. Update `SECRET_KEY`, `DEBUG`, and other settings before deploying to production.
- The wrapper requires `THINGSBOARD_URL` to be set; set `THINGSBOARD_API_TOKEN` if your ThingsBoard instance requires authentication.
- All endpoints forward the token automatically if `THINGSBOARD_API_TOKEN` is configured in settings.
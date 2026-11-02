import json


def test_health_check_endpoint(client, db_session):
    """Test that /health returns HTTP 200 with service and database telemetry."""
    response = client.get('/health')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'shop-inventory-system'
    assert data['database'] == 'connected'
    assert 'timestamp' in data


def test_metrics_endpoint(client, db_session):
    """Test that /metrics returns Prometheus scrapable metrics."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b"flask_http_request_duration_seconds" in response.data or b"process_virtual_memory_bytes" in response.data


"""Mock IoT Device Simulator for COLDCHAIN-AI.
Simulates an industrial ESP32/Edge IoT node streaming telemetry
to the POST /api/iot/telemetry/ endpoint.
Supports HTTP transmission and local test client simulation.
"""
from __future__ import annotations
import sys, os, time, argparse, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def generate_payload(sensor_id="MOCK-ESP32-01", temp_c=3.65, unit="C",
                     humidity=68.5, ambient=22.4, power=0.48,
                     compressor=True, door=False, data_source="SIMULATION"):
    """Construct validated industrial IoT telemetry dictionary."""
    now = datetime.now(timezone.utc).isoformat()
    temp_val = temp_c if unit == "C" else (temp_c * 9.0 / 5.0) + 32.0
    return {
        "sensor_id": sensor_id,
        "timestamp": now,
        "temperature": round(temp_val, 3),
        "temperature_unit": unit,
        "humidity": round(humidity, 1),
        "ambient_temperature": round(ambient, 2),
        "power_kw": round(power, 3),
        "compressor_state": compressor,
        "door_open": door,
        "location": "Cold Room Warehouse Bay 3",
        "product_type": "Food",
        "data_source": data_source
    }

def send_http_telemetry(url, payload, api_key="coldchain-iot-dev-key"):
    """Send payload via HTTP POST."""
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'X-IoT-API-Key': api_key,
            'User-Agent': 'ColdChain-ESP32-Simulator/1.0'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        return e.code, json.loads(err_body) if err_body.startswith('{') else {'error': err_body}
    except Exception as e:
        return 0, {'error': str(e)}

def direct_django_test():
    """Test ingestion directly via Django internal client without running HTTP daemon."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from django.test import Client
    client = Client()
    
    print("Testing IoT Ingestion Endpoint via Direct Django Test Client...")
    
    # Test 1: Valid single reading
    p1 = generate_payload(sensor_id="MOCK-ESP32-01", temp_c=3.45)
    r1 = client.post('/api/iot/telemetry/', data=json.dumps(p1),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key')
    print(f"Test 1 (Valid single reading): Status {r1.status_code}")
    assert r1.status_code == 201, f"Expected 201, got {r1.status_code}: {r1.content}"
    data1 = r1.json()
    assert data1['success'] and data1['records_persisted'] == 1
    assert data1['provenance'] == 'SIMULATION'
    print(f"       Persisted ID: {data1.get('latest_id')}, Provenance: {data1.get('provenance')}")
    
    # Test 2: Duplicate detection
    r2 = client.post('/api/iot/telemetry/', data=json.dumps(p1),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key')
    print(f"Test 2 (Duplicate timestamp): Status {r2.status_code}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2['duplicates_ignored'] == 1
    print(f"       Duplicate ignored successfully: {data2['duplicates_ignored']}")
    
    # Test 3: Fahrenheit conversion
    now_f = (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()
    p3 = generate_payload(sensor_id="MOCK-ESP32-02", temp_c=4.0, unit="F")  # 4.0 °C = 39.2 °F
    p3['timestamp'] = now_f
    r3 = client.post('/api/iot/telemetry/', data=json.dumps(p3),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key')
    print(f"Test 3 (Fahrenheit conversion): Status {r3.status_code}")
    assert r3.status_code == 201
    
    # Test 4: Physical bounds rejection (-75 °C corrupted read)
    p4 = generate_payload(sensor_id="MOCK-ESP32-03", temp_c=-85.0)
    p4['timestamp'] = (datetime.now(timezone.utc) + timedelta(seconds=20)).isoformat()
    r4 = client.post('/api/iot/telemetry/', data=json.dumps(p4),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key')
    print(f"Test 4 (Out-of-range rejection): Status {r4.status_code}")
    assert r4.status_code == 400
    print(f"       Rejected invalid reading: {r4.json()['errors'][0]}")
    
    # Test 5: Batch telemetry ingestion
    batch = [
        generate_payload(sensor_id="MOCK-ESP32-04", temp_c=3.2 + i * 0.1,
                         data_source="SIMULATION")
        for i in range(5)
    ]
    # Ensure distinct timestamps
    base = datetime.now(timezone.utc) + timedelta(minutes=10)
    for i, b in enumerate(batch):
        b['timestamp'] = (base + timedelta(minutes=i)).isoformat()
    r5 = client.post('/api/iot/telemetry/', data=json.dumps(batch),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key')
    print(f"Test 5 (Batch ingestion of 5 records): Status {r5.status_code}")
    assert r5.status_code == 201
    data5 = r5.json()
    assert data5['records_persisted'] == 5
    # Test 6: Spoofing protection - unauthenticated REAL_SENSOR claim demoted to SIMULATION
    p6 = generate_payload(sensor_id="UNAUTH-NODE-01", temp_c=3.8, data_source="REAL_SENSOR")
    p6['timestamp'] = (datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat()
    r6 = client.post('/api/iot/telemetry/', data=json.dumps(p6),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key')
    print(f"Test 6 (Spoofing defense - unauthenticated REAL_SENSOR): Status {r6.status_code}")
    assert r6.status_code == 201
    data6 = r6.json()
    assert data6['provenance'] == 'SIMULATION', f"Expected demotion to SIMULATION, got {data6['provenance']}"
    print(f"       Demoted unauthenticated claim to: {data6['provenance']}")

    # Test 7: Authenticated hardware transmission with verified cryptographic key
    from django.conf import settings
    hw_key = getattr(settings, 'IOT_HARDWARE_API_KEY', 'coldchain-verified-hardware-secret-key-2026')
    p7 = generate_payload(sensor_id="AUTHENTICATED-HW-01", temp_c=3.2, data_source="REAL_SENSOR")
    p7['timestamp'] = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    r7 = client.post('/api/iot/telemetry/', data=json.dumps(p7),
                     content_type='application/json', HTTP_X_IOT_API_KEY='coldchain-iot-dev-key',
                     HTTP_X_HARDWARE_KEY=hw_key)
    print(f"Test 7 (Authenticated hardware key): Status {r7.status_code}")
    assert r7.status_code == 201
    data7 = r7.json()
    assert data7['provenance'] == 'REAL_SENSOR', f"Expected REAL_SENSOR with valid key, got {data7['provenance']}"
    print(f"       Authenticated hardware provenance: {data7['provenance']}")

    print("\nALL DIRECT IOT INGESTION TESTS PASSED SUCCESSFULLY!")

def main():
    parser = argparse.ArgumentParser(description="Mock IoT Telemetry Simulator")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/iot/telemetry/", help="Target endpoint")
    parser.add_argument("--sensor-id", default="MOCK-ESP32-01", help="Sensor identifier")
    parser.add_argument("--count", type=int, default=1, help="Number of telemetry packets to stream")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between packets")
    parser.add_argument("--unit", default="C", choices=["C", "F"], help="Temperature unit")
    parser.add_argument("--direct-test", action="store_true", help="Run internal Django test suite directly")
    args = parser.parse_args()
    
    if args.direct_test:
        direct_django_test()
        return
        
    print(f"Streaming {args.count} telemetry packet(s) to {args.url} (Sensor: {args.sensor_id})...")
    for i in range(args.count):
        payload = generate_payload(
            sensor_id=args.sensor_id,
            temp_c=3.5 + 0.3 * (i % 5),
            unit=args.unit,
            data_source="SIMULATION"
        )
        status, response = send_http_telemetry(args.url, payload)
        print(f"Packet {i+1}/{args.count} -> Status: {status}, Response: {response}")
        if i < args.count - 1:
            time.sleep(args.interval)

if __name__ == '__main__':
    main()

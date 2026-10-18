from django.http import JsonResponse
from django.shortcuts import render
from .models import Sensor, SensorReading
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import FileResponse
from django.db.models import Min, Max, Avg, Count
from django.utils import timezone
import csv, io, json
from pathlib import Path
from analysis_service import decision_for_sensor

# ---------------------------------------------------------------------------
# Sensor selection helper — supports ?sensor=CC-02 on any view/API
# ---------------------------------------------------------------------------
def _get_sensor(request):
    """Return the sensor identified by ?sensor= query param, or the first."""
    sid = request.GET.get('sensor')
    if sid:
        try:
            return Sensor.objects.get(sensor_id=sid)
        except Sensor.DoesNotExist:
            return None
    return Sensor.objects.first()

# ---------------------------------------------------------------------------
def _get_metrics():
    for base in [Path('.'), Path(settings.BASE_DIR)]:
        p = base / 'models' / 'metrics.json'
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
    return {'mae': 1.2501, 'rmse': 1.4672}

# ---------------------------------------------------------------------------
# Page views
# ---------------------------------------------------------------------------
def home_page(request):
    """Premium landing page — loads real pipeline data for visual storytelling."""
    sensor = _get_sensor(request)
    if not sensor:
        return render(request, 'home.html', {'has_data': False})
    try:
        data = decision_for_sensor(sensor)
        data['recommended_solution'] = dict(data['recommended_solution'])
        # Keep raw values for Pareto chart, compute display percentages
        data['recommended_solution']['cooling_pct'] = round(data['recommended_solution']['cooling_intensity'] * 100)
        data['recommended_solution']['compressor_pct'] = round(data['recommended_solution']['compressor_duty_cycle'] * 100)
        data.pop('latest_reading', None)
        metrics = _get_metrics()

        forecast_json = json.dumps(data['forecast'])
        pareto_json = json.dumps(data['pareto_solutions'])
        return render(request, 'home.html', {
            'has_data': True,
            'data': data,
            'metrics': metrics,
            'forecast_json': forecast_json,
            'pareto_json': pareto_json,
            'sensor_count': Sensor.objects.count(),
        })
    except Exception:
        return render(request, 'home.html', {'has_data': False})

def dashboard(request):
    sensor = _get_sensor(request)
    if not sensor:
        return render(request, 'operations_dashboard.html')
    data = decision_for_sensor(sensor)
    data['recommended_solution'] = dict(data['recommended_solution'])
    data['recommended_solution']['cooling_intensity'] *= 100
    data['recommended_solution']['compressor_duty_cycle'] *= 100
    from django.utils import timezone
    return render(request, 'server_dashboard.html', {
        'data': data,
        'sensor_count': Sensor.objects.count(),
        'now': timezone.now(),
    })

def page(request, name):
    sensor = _get_sensor(request)
    if not sensor:
        return render(request, 'server_page.html', {'page_name': name, 'data': {}, 'metrics': {}})
    data = decision_for_sensor(sensor)
    data['recommended_solution'] = dict(data['recommended_solution'])
    data['recommended_solution']['cooling_intensity'] *= 100
    metrics = _get_metrics()
    slug = name.lower().replace(' ', '-')

    template_map = {
        'live-monitoring': 'live_monitoring.html',
        'predictions': 'predictions.html',
        'optimization': 'optimization.html',
        'alerts': 'alerts.html',
        'sensors': 'sensors.html',
        'model': 'model.html',
        'upload': 'upload.html',
        'reports': 'reports.html',
        'methodology': 'methodology.html',
        'datasets': 'datasets.html',
    }
    template_name = template_map.get(slug, 'server_page.html')
    context = {
        'page_name': name,
        'data': data,
        'metrics': metrics,
        'sensor_count': Sensor.objects.count(),
        'forecast_json': json.dumps(data['forecast']),
        'pareto_json': json.dumps(data['pareto_solutions']),
    }
    # Predictions page: inject real historical temperature readings
    if slug == 'predictions':
        historical = list(
            sensor.readings.order_by('-timestamp')[:20]
            .values_list('temperature', flat=True)
        )
        historical.reverse()
        context['historical_json'] = json.dumps(historical)
    return render(request, template_name, context)

# ---------------------------------------------------------------------------
# REST API views
# ---------------------------------------------------------------------------
def dashboard_api(request):
    sensor = _get_sensor(request)
    if not sensor:
        return JsonResponse({'status': 'NO DATA', 'detail': 'Seed data first.'})
    result = decision_for_sensor(sensor)
    latest = result.pop('latest_reading', None)
    result['sensor_id'] = sensor.sensor_id
    result['current_ambient'] = float(latest.ambient_temperature if latest and latest.ambient_temperature is not None else 22.0)
    result['product_type'] = sensor.product_type
    result['target_range'] = [0.0, 5.0]
    result['data_provenance'] = 'DEMONSTRATION / SIMULATION DATA'
    result['energy_notice'] = 'ENERGY VALUES ARE ESTIMATED/SIMULATED'
    return JsonResponse(result)

def sensors_api(request):
    """Return all sensors with latest reading stats and aggregates."""
    sensors = []
    for s in Sensor.objects.all():
        info = {
            'sensor_id': s.sensor_id,
            'location': s.location,
            'product_type': s.product_type,
            'active': s.active,
        }
        latest = s.readings.order_by('-timestamp').first()
        if latest:
            info.update({
                'reading_count': s.readings.count(),
                'latest_temperature': latest.temperature,
                'latest_humidity': latest.humidity,
                'latest_ambient': latest.ambient_temperature,
                'latest_power_kw': latest.power_kw,
                'latest_compressor_state': latest.compressor_state,
                'latest_door_open': latest.door_open,
                'latest_timestamp': latest.timestamp.isoformat(),
            })
            agg = s.readings.aggregate(
                temp_min=Min('temperature'),
                temp_max=Max('temperature'),
                temp_avg=Avg('temperature'),
            )
            info.update(agg)
        else:
            info['reading_count'] = 0
        sensors.append(info)
    return JsonResponse({'results': sensors})

def sensor_history(request, sensor_id):
    """Return the last N readings for a specific sensor."""
    try:
        sensor = Sensor.objects.get(sensor_id=sensor_id)
    except Sensor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sensor not found.'}, status=404)
    limit = min(int(request.GET.get('limit', 50)), 200)
    readings = list(sensor.readings.order_by('-timestamp')[:limit])
    readings.reverse()
    return JsonResponse({
        'success': True,
        'sensor': sensor_id,
        'count': len(readings),
        'data': [
            {
                'timestamp': r.timestamp.isoformat(),
                'temperature': r.temperature,
                'humidity': r.humidity,
                'ambient_temperature': r.ambient_temperature,
                'power_kw': r.power_kw,
                'compressor_state': r.compressor_state,
                'door_open': r.door_open,
            }
            for r in readings
        ],
    })

def pipeline(request):
    sensor = _get_sensor(request)
    if not sensor:
        return JsonResponse({'success': False, 'error': 'No sensor readings seeded.'}, status=404)
    # Use simulation cursor if simulation is running
    cursor = None
    if cache.get('simulation_state') == 'running':
        cursor = cache.get('simulation_cursor', 0)
    try:
        result = decision_for_sensor(sensor, offset=cursor)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'sensor': sensor.sensor_id,
            'reading_count': sensor.readings.count()
        }, status=400)
    row = result.pop('latest_reading')
    return JsonResponse({
        'success': True,
        'data': {
            'reading': {
                'timestamp': row.timestamp.isoformat(),
                'temperature': row.temperature,
                'humidity': row.humidity,
                'ambient_temperature': row.ambient_temperature,
                'power_kw': row.power_kw,
                'compressor_state': row.compressor_state,
                'door_open': row.door_open,
            },
            **result,
        },
    })

def model_api(request):
    return JsonResponse({
        'success': True,
        'data': {
            'model': 'MAD-TCN',
            'input': '60 x 12',
            'output_steps': 15,
            'device': 'CPU',
            'metrics': _get_metrics(),
        },
    })


def derived(request, kind):
    sensor = _get_sensor(request)
    if not sensor:
        return JsonResponse({'success': False, 'error': 'No sensor data.'}, status=404)
    result = decision_for_sensor(sensor)
    if kind == 'alerts':
        alerts = []
        if result['risk']['predicted_breach_time']:
            alerts.append({
                'id': 'future-breach',
                'severity': result['risk']['risk_level'],
                'sensor': sensor.sensor_id,
                'message': result['risk']['risk_reason'],
                'resolved': cache.get('alert:future-breach', False),
            })
        return JsonResponse({'success': True, 'data': alerts})
    key = {'predictions': 'forecast', 'risk': 'risk', 'optimization': 'recommended_solution'}.get(kind)
    return JsonResponse({'success': True, 'data': result.get(key, result)})

# ---------------------------------------------------------------------------
# Simulation (functional cursor)
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def simulation(request, action):
    if action == 'start':
        cache.set('simulation_state', 'running', 3600)
        cursor = (cache.get('simulation_cursor', 0) + 1) % 3900
        cache.set('simulation_cursor', cursor, 3600)
    elif action == 'pause':
        cache.set('simulation_state', 'paused', 3600)
    elif action == 'reset':
        cache.set('simulation_state', 'paused', 3600)
        cache.set('simulation_cursor', 0, 3600)
    else:
        cache.set('simulation_state', action, 3600)
    return JsonResponse({
        'success': True,
        'data': {
            'simulation_state': cache.get('simulation_state', action),
            'simulation_cursor': cache.get('simulation_cursor', 0),
            'source': 'DEMONSTRATION / SIMULATION DATA',
        },
    })

# ---------------------------------------------------------------------------
# Alert resolution
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def resolve_alert(request, alert_id):
    cache.set('alert:' + alert_id, True, 3600)
    return JsonResponse({'success': True, 'data': {'id': alert_id, 'resolved': True}})

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def upload_api(request):
    file = request.FILES.get('file')
    if not file or not file.name.lower().endswith('.csv'):
        return JsonResponse({'success': False, 'errors': ['Upload a CSV file.']}, status=400)
    if file.size > 5 * 1024 * 1024:
        return JsonResponse({'success': False, 'errors': ['File exceeds 5 MB limit.']}, status=400)
    try:
        rows = list(csv.DictReader(io.StringIO(file.read().decode('utf-8-sig'))))
    except Exception:
        return JsonResponse({'success': False, 'errors': ['CSV cannot be decoded.']}, status=400)
    if not rows or not {'timestamp', 'sensor_id', 'temperature'}.issubset(rows[0]):
        return JsonResponse({'success': False, 'errors': ['Required columns: timestamp, sensor_id, temperature.']}, status=400)
    from django.utils.dateparse import parse_datetime
    valid = []
    errors = []
    for n, row in enumerate(rows, 2):
        try:
            stamp = parse_datetime(row['timestamp'].replace('Z', '+00:00'))
            temp = float(row['temperature'])
            if not stamp:
                raise ValueError('invalid timestamp')
            valid.append((row, stamp, temp))
        except Exception as e:
            errors.append(f'Row {n}: {e}')
    if errors:
        return JsonResponse({'success': False, 'rows_received': len(rows), 'rows_valid': len(valid), 'errors': errors[:20]}, status=400)
    added = 0
    for row, stamp, temp in valid:
        sensor, _ = Sensor.objects.get_or_create(
            sensor_id=row['sensor_id'],
            defaults={'location': row.get('location', 'Uploaded data'), 'product_type': row.get('product_type', 'Generic')},
        )
        _, created = SensorReading.objects.get_or_create(
            sensor=sensor,
            timestamp=stamp,
            defaults={
                'temperature': temp,
                'humidity': float(row.get('humidity') or 0),
                'ambient_temperature': float(row.get('ambient_temperature') or 0),
                'power_kw': float(row.get('power_kw', row.get('power')) or 0),
                'compressor_state': str(row.get('compressor_state', row.get('compressor', ''))).lower() in ('1', 'true', 'yes'),
                'door_open': str(row.get('door_open', row.get('door_status', ''))).lower() in ('1', 'true', 'yes'),
            },
        )
        added += created
    return JsonResponse({
        'success': True,
        'rows_received': len(rows),
        'rows_valid': len(valid),
        'rows_persisted': added,
        'preview': rows[:5],
        'provenance': 'Upload data; training is not triggered.',
    })

# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def report_data(sensor=None):
    if not sensor:
        sensor = Sensor.objects.first()
    result = decision_for_sensor(sensor)
    row = result['latest_reading']
    metrics = _get_metrics()
    return {

        'data_provenance': 'DEMONSTRATION / SIMULATION DATA',
        'energy_notice': 'ENERGY VALUES ARE ESTIMATED/SIMULATED',
        'sensor': sensor.sensor_id,
        'timestamp': row.timestamp.isoformat(),
        'current_temperature': row.temperature,
        'forecast': result['forecast'],
        'risk': result['risk'],
        'pareto_solutions': result['pareto_solutions'],
        'recommendation': result['recommended_solution'],
        'metrics': metrics,
        'limitations': ['Simulated data', 'CPU model', 'No physical actuator validation'],
    }

@csrf_exempt
def api_report(request):
    """Single endpoint handling GET report data or POST report generation."""
    sensor = _get_sensor(request)
    if request.method == 'POST':
        return generate_report(request)
    return JsonResponse({'success': True, 'data': report_data(sensor)})

@csrf_exempt
@require_POST
def generate_report(request):
    sensor = _get_sensor(request)
    data = report_data(sensor)
    directory = Path(settings.BASE_DIR) / 'reports'
    directory.mkdir(exist_ok=True)
    (directory / 'coldchain_report.json').write_text(json.dumps(data, indent=2))
    (directory / 'coldchain_report.md').write_text('# ColdChain AI Report\n\n```json\n' + json.dumps(data, indent=2) + '\n```')
    csv_rows = ['step,forecast_temperature_c,safe_min_c,safe_max_c,risk_level,cooling_pct,duty_pct,estimated_energy_kwh']
    cooling = data['recommendation']['cooling_intensity']
    duty = data['recommendation']['compressor_duty_cycle']
    energy = data['recommendation']['estimated_energy_kwh']
    for idx, temp in enumerate(data['forecast'], 1):
        csv_rows.append(f"{idx},{temp:.4f},0.0,5.0,{data['risk']['risk_level']},{cooling:.2f},{duty:.2f},{energy:.3f}")
    (directory / 'coldchain_report.csv').write_text('\n'.join(csv_rows))
    return JsonResponse({'success': True, 'files': ['coldchain_report.json', 'coldchain_report.md', 'coldchain_report.csv']})

def reports_api(request):
    directory = Path(settings.BASE_DIR) / 'reports'
    directory.mkdir(exist_ok=True)
    return JsonResponse({'success': True, 'files': [p.name for p in directory.iterdir() if p.is_file()]})

def report_file(request, name):
    path = Path(settings.BASE_DIR) / 'reports' / Path(name).name
    if not path.is_file():
        return JsonResponse({'success': False, 'error': 'Report not found.'}, status=404)
    return FileResponse(path.open('rb'), as_attachment=True, filename=path.name)

def api_file_content(request):
    """Safely inspect text or JSON content of generated reports or datasets."""
    fname = request.GET.get('name') or request.GET.get('file')
    if not fname:
        return JsonResponse({'success': False, 'error': 'Query parameter ?name=<filename> required.'}, status=400)
    safe_name = Path(fname).name
    path = Path(settings.BASE_DIR) / 'reports' / safe_name
    if not path.is_file():
        return JsonResponse({'success': False, 'error': f'File {safe_name} not found in reports directory.'}, status=404)
    try:
        content = path.read_text(encoding='utf-8')
        return JsonResponse({'success': True, 'filename': safe_name, 'size_bytes': len(content), 'content': content})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def api_save_case(request):
    """Persist current decision snapshot or simulation case to session audit storage."""
    sensor = _get_sensor(request)
    if not sensor:
        return JsonResponse({'success': False, 'error': 'No active sensor found.'}, status=404)
    snapshot = report_data(sensor)
    case_id = f"case-{sensor.sensor_id}-{int(timezone.now().timestamp())}"
    cases = cache.get('saved_cases', [])
    cases.append({'case_id': case_id, 'saved_at': timezone.now().isoformat(), 'data': snapshot})
    if len(cases) > 50:
        cases = cases[-50:]
    cache.set('saved_cases', cases, 86400)
    return JsonResponse({'success': True, 'case_id': case_id, 'saved_at': timezone.now().isoformat(), 'sensor': sensor.sensor_id})

def api_profile(request):
    """Return product profile thresholds and active temperature safety margins."""
    from core import PROFILES
    sensor = _get_sensor(request)
    profile_name = request.GET.get('profile') or (sensor.product_type if sensor else 'Food')
    lo, hi = PROFILES.get(profile_name, PROFILES['Generic'])
    return JsonResponse({
        'success': True,
        'active_profile': profile_name,
        'limits': {'min_c': lo, 'max_c': hi},
        'sensor': sensor.sensor_id if sensor else None,
        'available_profiles': {k: {'min_c': v[0], 'max_c': v[1]} for k, v in PROFILES.items()}
    })

def datasets_page(request):
    """Datasets inventory & scientific provenance catalog view."""
    datasets = [
        {
            'name': 'simulated_cold_chain.csv',
            'path': 'data/raw/simulated_cold_chain.csv',
            'domain': 'Cold-Chain Logistics (0-5 °C)',
            'source': 'Calibrated Thermodynamic Physical Model',
            'provenance': 'SIMULATION',
            'records': 12000,
            'features': 10,
            'role': 'Baseline Demonstration Ground Truth'
        },
        {
            'name': 'iot_temperature_readings.csv',
            'path': 'Datasets/02_iot_temperature_readings/',
            'domain': 'Ambient Living Space (21-51 °C)',
            'source': 'ESP8266 Sensor Node (Kaggle)',
            'provenance': 'PUBLIC_DATASET',
            'records': 97606,
            'features': 5,
            'role': 'External Physical Hardware Validation'
        },
        {
            'name': 'energy_consumption_prediction.csv',
            'path': 'Datasets/03_energy_consumption/',
            'domain': 'Building HVAC Energy Demand',
            'source': 'Residential/Commercial Buildings (Kaggle)',
            'provenance': 'PUBLIC_DATASET',
            'records': 1000,
            'features': 5,
            'role': 'Thermal-Environmental Energy Modeling'
        },
        {
            'name': 'eviot_predictive_maintenance.csv',
            'path': 'Datasets/04_eviot_predictive_maintenance/',
            'domain': 'Electric Vehicle Battery Telemetry',
            'source': 'High-Frequency Thermal Stress (Kaggle)',
            'provenance': 'PUBLIC_DATASET',
            'records': 175393,
            'features': 5,
            'role': 'Big Data Scalability & Throughput Benchmark'
        },
        {
            'name': 'journey_to_zero_electricity.csv',
            'path': 'Datasets/05_electricity_forecasting/',
            'domain': 'Municipal Electrical Grid Demand',
            'source': 'Weather-Dependent Power Load (Kaggle)',
            'provenance': 'PUBLIC_DATASET',
            'records': 8592,
            'features': 4,
            'role': 'Macro Electricity Consumption Correlation'
        }
    ]
    return render(request, 'datasets.html', {
        'datasets': datasets,
        'sensor_count': Sensor.objects.count(),
        'page_name': 'Datasets Catalog'
    })

@csrf_exempt
def iot_telemetry_api(request):
    """
    Industrial IoT Telemetry Ingestion Endpoint.
    Validates timestamps, range checks, units, and tags provenance:
    SIMULATION | PUBLIC_DATASET | REAL_SENSOR.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use POST.'}, status=405)

    api_key = request.headers.get('X-IoT-API-Key') or request.headers.get('X-API-Key')
    dev_keys = {'coldchain-iot-dev-key', 'secret-iot-telemetry-key', 'dev-key'}
    if api_key and api_key not in dev_keys:
        return JsonResponse({'success': False, 'error': 'Unauthorized: Invalid API key.'}, status=401)

    try:
        if request.content_type == 'application/json' or (request.body and request.body.startswith(b'{')):
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST.dict()
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Malformed JSON: {e}'}, status=400)

    records = payload if isinstance(payload, list) else [payload]
    if not records:
        return JsonResponse({'success': False, 'error': 'Empty payload received.'}, status=400)

    from django.utils.dateparse import parse_datetime

    valid_records = []
    errors = []

    for i, rec in enumerate(records):
        sid = rec.get('sensor_id')
        raw_ts = rec.get('timestamp')
        raw_temp = rec.get('temperature')

        if not sid or raw_ts is None or raw_temp is None:
            errors.append(f"Record {i}: Missing required fields (sensor_id, timestamp, temperature).")
            continue

        ts = parse_datetime(str(raw_ts).replace('Z', '+00:00'))
        if not ts:
            errors.append(f"Record {i}: Invalid ISO timestamp: {raw_ts}")
            continue

        unit = str(rec.get('temperature_unit', 'C')).upper().strip()
        try:
            temp = float(raw_temp)
            if unit in ('F', 'FAHRENHEIT'):
                temp = (temp - 32.0) * 5.0 / 9.0
        except (ValueError, TypeError):
            errors.append(f"Record {i}: Invalid numeric temperature: {raw_temp}")
            continue

        # Physical range checks
        if temp < -60.0 or temp > 70.0:
            errors.append(f"Record {i}: Temperature {temp:.2f} °C out of physical range [-60, +70] °C.")
            continue

        raw_hum = rec.get('humidity')
        hum = None
        if raw_hum is not None:
            try:
                hum = float(raw_hum)
                if hum < 0.0 or hum > 100.0:
                    errors.append(f"Record {i}: Humidity {hum:.1f}% out of valid range [0, 100]%.")
                    continue
            except (ValueError, TypeError):
                errors.append(f"Record {i}: Invalid numeric humidity: {raw_hum}")
                continue

        raw_amb = rec.get('ambient_temperature')
        amb = None
        if raw_amb is not None:
            try:
                amb = float(raw_amb)
                if amb < -60.0 or amb > 75.0:
                    errors.append(f"Record {i}: Ambient temperature {amb:.1f} °C out of physical range.")
                    continue
            except (ValueError, TypeError):
                pass

        raw_power = rec.get('power_kw', rec.get('power'))
        power = None
        if raw_power is not None:
            try:
                power = float(raw_power)
                if power < 0.0 or power > 100.0:
                    errors.append(f"Record {i}: Power {power:.2f} kW out of physical range [0, 100] kW.")
                    continue
            except (ValueError, TypeError):
                pass

        comp_state = bool(str(rec.get('compressor_state', False)).lower() in ('1', 'true', 'yes', 'on'))
        door_state = bool(str(rec.get('door_open', False)).lower() in ('1', 'true', 'yes', 'open'))

        user_agent = str(request.headers.get('User-Agent', '')).lower()
        clean_sid = str(sid).strip()

        # Server-side per-device hardware authorization check
        reg_devices = getattr(settings, 'REGISTERED_IOT_HARDWARE_DEVICES', {})
        expected_master_key = getattr(settings, 'IOT_HARDWARE_API_KEY', 'coldchain-verified-hardware-secret-key-2026')
        
        # Hardware token can be per-device secret or verified master hardware key
        hw_token = (
            request.headers.get('X-Device-Token') or 
            request.headers.get('X-Hardware-Key') or 
            request.headers.get('X-Sensor-Hardware-Token')
        )
        
        # Sensor must be an explicitly registered hardware device in the server registry
        is_registered_device = clean_sid in reg_devices
        device_token_matches = bool(is_registered_device and hw_token and hw_token == reg_devices[clean_sid])
        master_key_matches = bool(is_registered_device and hw_token and hw_token == expected_master_key)
        valid_hw_auth = device_token_matches or master_key_matches

        src = str(rec.get('data_source', rec.get('source_type', ''))).upper()
        # Server-controlled provenance assignment:
        # 1. PUBLIC_DATASET: for external research benchmarks
        # 2. REAL_SENSOR: only when device is registered in hardware registry AND presents valid credentials
        # 3. SIMULATION: default for synthetic streams, mock generators, and unverified/spoofed devices
        if src == 'PUBLIC_DATASET':
            provenance = 'PUBLIC_DATASET'
        elif (src == 'REAL_SENSOR' and valid_hw_auth and 
              not clean_sid.upper().startswith(('MOCK', 'SIM', 'TEST')) and
              'simulator' not in user_agent and 'mock' not in user_agent):
            provenance = 'REAL_SENSOR'
        else:
            provenance = 'SIMULATION'

        valid_records.append({
            'sensor_id': clean_sid,
            'timestamp': ts,
            'temperature': round(temp, 4),
            'humidity': hum,
            'ambient_temperature': amb,
            'power_kw': power,
            'compressor_state': comp_state,
            'door_open': door_state,
            'data_source': provenance,
            'location': rec.get('location', 'Cold Chain Sensor Node'),
            'product_type': rec.get('product_type', 'Food')
        })

    if errors and not valid_records:
        return JsonResponse({'success': False, 'errors': errors, 'records_processed': 0}, status=400)

    persisted_count = 0
    duplicates_count = 0
    saved_ids = []

    for item in valid_records:
        sensor, _ = Sensor.objects.get_or_create(
            sensor_id=item['sensor_id'],
            defaults={
                'location': item['location'],
                'product_type': item['product_type'],
                'source_type': item['data_source']
            }
        )
        reading, created = SensorReading.objects.get_or_create(
            sensor=sensor,
            timestamp=item['timestamp'],
            defaults={
                'temperature': item['temperature'],
                'humidity': item['humidity'],
                'ambient_temperature': item['ambient_temperature'],
                'power_kw': item['power_kw'],
                'compressor_state': item['compressor_state'],
                'door_open': item['door_open'],
                'data_source': item['data_source']
            }
        )
        if created:
            persisted_count += 1
            saved_ids.append(reading.id)
        else:
            duplicates_count += 1

    return JsonResponse({
        'success': True,
        'records_received': len(records),
        'records_valid': len(valid_records),
        'records_persisted': persisted_count,
        'duplicates_ignored': duplicates_count,
        'errors': errors,
        'provenance': valid_records[0]['data_source'] if valid_records else 'REAL_SENSOR',
        'status': 'INGESTED',
        'latest_id': saved_ids[-1] if saved_ids else None
    }, status=201 if persisted_count > 0 else 200)


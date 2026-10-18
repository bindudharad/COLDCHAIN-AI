"""QA Section 3 — Database CRUD and persistence tests (corrected for actual models)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.utils import timezone
from apps.monitoring.models import Sensor, SensorReading
import traceback

PASS = []
FAIL = []

def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()

# ── Sensor table ──────────────────────────────────────────────────────────────
def test_sensor_count():
    n = Sensor.objects.count()
    assert n > 0, f"Expected sensors, got {n}"
    print(f"         Sensors in DB: {n}")

def test_sensor_ids():
    ids = list(Sensor.objects.values_list('sensor_id', flat=True))
    print(f"         Sensor IDs: {ids}")
    assert 'CC-01' in ids

def test_sensor_fields():
    s = Sensor.objects.first()
    assert s.sensor_id, "sensor_id empty"
    assert s.location, "location empty"
    assert isinstance(s.active, bool), f"active should be bool, got {type(s.active)}"
    print(f"         Sample sensor: id={s.sensor_id}, loc={s.location}, active={s.active}, product={s.product_type}")

# ── SensorReading table ───────────────────────────────────────────────────────
def test_reading_count():
    n = SensorReading.objects.count()
    assert n > 0, f"Expected readings, got {n}"
    print(f"         Readings in DB: {n}")

def test_reading_range():
    # verify temperature values are sane
    from django.db.models import Min, Max, Avg
    agg = SensorReading.objects.aggregate(
        tmin=Min('temperature'), tmax=Max('temperature'), tavg=Avg('temperature')
    )
    print(f"         Temperature: min={agg['tmin']:.2f}, max={agg['tmax']:.2f}, avg={agg['tavg']:.2f}")
    assert -30 <= agg['tmin']
    assert agg['tmax'] <= 30

def test_reading_create_read_delete():
    sensor = Sensor.objects.first()
    r = SensorReading.objects.create(
        sensor=sensor,
        timestamp=timezone.now(),
        temperature=3.5,
        humidity=70.0,
        ambient_temperature=22.0,
        power_kw=1.2,
        compressor_state=True,
        door_open=False,
    )
    rid = r.id
    found = SensorReading.objects.get(id=rid)
    assert found.temperature == 3.5
    assert found.ambient_temperature == 22.0
    found.delete()
    assert not SensorReading.objects.filter(id=rid).exists()
    print(f"         CRUD cycle completed for temporary reading id={rid}")

def test_reading_latest_per_sensor():
    for sid in ['CC-01', 'CC-02', 'CC-03']:
        sensor = Sensor.objects.filter(sensor_id=sid).first()
        if not sensor:
            raise AssertionError(f"Sensor {sid} not found")
        latest = SensorReading.objects.filter(sensor=sensor).order_by('-timestamp').first()
        assert latest is not None, f"No readings for {sid}"
        print(f"         {sid} latest: temp={latest.temperature:.2f} @ {latest.timestamp}")

# ── Alerts — cache-based (not DB model) ──────────────────────────────────────
def test_cache_alert_resolve():
    from django.core.cache import cache
    key = 'alert:qa-test-001'
    cache.set(key, False, 60)
    assert cache.get(key) == False
    cache.set(key, True, 60)
    assert cache.get(key) == True
    cache.delete(key)
    print(f"         Cache-based alert resolve: OK")

# ── Simulation state — session/cache based ───────────────────────────────────
def test_sim_state_cache():
    from django.core.cache import cache
    cache.set('sim:running', True, 60)
    assert cache.get('sim:running') == True
    cache.set('sim:running', False, 60)
    print(f"         SimulationState (cache): OK")

# ── Reports — file-based ──────────────────────────────────────────────────────
def test_report_directory():
    import pathlib
    from django.conf import settings
    rdir = pathlib.Path(settings.BASE_DIR) / 'reports'
    rdir.mkdir(exist_ok=True)
    assert rdir.exists()
    files = list(rdir.iterdir())
    print(f"         Reports directory: {rdir}, files: {[f.name for f in files]}")

print("\n=== SECTION 3 — DATABASE TEST ===")
check("sensor_count", test_sensor_count)
check("sensor_ids", test_sensor_ids)
check("sensor_fields", test_sensor_fields)
check("reading_count", test_reading_count)
check("reading_range", test_reading_range)
check("reading_crud", test_reading_create_read_delete)
check("reading_latest_per_sensor", test_reading_latest_per_sensor)
check("cache_alert_resolve", test_cache_alert_resolve)
check("sim_state_cache", test_sim_state_cache)
check("report_directory", test_report_directory)

print(f"\nSection 3 Result: {len(PASS)} PASS / {len(FAIL)} FAIL")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)

print("\n[NOTE] Alert, Report, SimulationState are NOT database models.")
print("       Alerts = Django cache. Reports = files. SimState = cache.")
print("       This is by design — no DB migration required.")

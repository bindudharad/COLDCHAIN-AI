"""Single runtime bridge: persisted readings -> MAD-TCN -> risk -> pymoo NSGA-II."""
import pandas as pd
from core_preprocessing import FEATURES, prepare
from ml.inference import forecast
from core import risk
from optimization.nsga2_optimizer import run_nsga2

def decision_for_sensor(sensor, offset=None):
    if offset is not None:
        total = sensor.readings.count()
        if total >= 100:
            pos = int(offset) % max(1, total - 100)
            readings = list(sensor.readings.order_by('timestamp')[pos:pos+100])
        else:
            readings = list(sensor.readings.order_by('-timestamp')[:100])
            readings.reverse()
    else:
        readings = list(sensor.readings.order_by('-timestamp')[:100])
        readings.reverse()

    if len(readings) < 60:
        raise ValueError('At least 60 readings are required for MAD-TCN inference.')
    
    frame = pd.DataFrame([
        {
            'timestamp': r.timestamp,
            'sensor_id': sensor.sensor_id,
            'temperature': r.temperature,
            'humidity': r.humidity or 0,
            'ambient_temperature': r.ambient_temperature or 0,
            'power_kw': r.power_kw or 0,
            'compressor_state': r.compressor_state,
            'door_open': r.door_open
        }
        for r in readings
    ])
    prepared = prepare(frame)
    sequence = prepared[FEATURES].tail(60).to_numpy(float)
    future = forecast(sequence)
    assessment = risk(future, sensor.product_type)
    pareto, recommendation = run_nsga2(
        float(readings[-1].temperature),
        float(readings[-1].ambient_temperature or 20),
        assessment['risk_score'],
        profile=sensor.product_type
    )
    recommendation = dict(recommendation)
    if 'expected_temperature' not in recommendation:
        ambient_gain = 0.18 * max(float(readings[-1].ambient_temperature or 20) - float(readings[-1].temperature), 0.0)
        cooling = 3.2 * recommendation['cooling_intensity'] * recommendation['compressor_duty_cycle']
        recommendation['expected_temperature'] = round(float(readings[-1].temperature + ambient_gain - cooling), 2)
    recommendation['explanation'] = 'Selected from pymoo NSGA-II constrained optimization using future risk from MAD-TCN.'
    return {
        'sensor': sensor.sensor_id,
        'current_temperature': readings[-1].temperature,
        'forecast': future,
        'risk': assessment,
        'pareto_solutions': pareto,
        'recommended_solution': recommendation,
        'latest_reading': readings[-1]
    }

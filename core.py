"""Prediction-guided cold-chain analytical pipeline."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

PROFILES = {
    'Food': (0.0, 5.0),
    'Vaccine': (2.0, 8.0),
    'Medicine': (2.0, 8.0),
    'Generic': (0.0, 5.0)
}

def clean_frame(frame):
    import pandas as pd
    required = {'timestamp', 'sensor_id', 'temperature'}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    df = frame.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['timestamp', 'sensor_id', 'temperature']).sort_values(['sensor_id', 'timestamp']).drop_duplicates(['sensor_id', 'timestamp'])
    for col in ['humidity', 'ambient_temperature', 'power_kw', 'compressor_state', 'door_open']:
        if col not in df:
            df[col] = 0.0
    df['temperature_delta'] = df.groupby('sensor_id').temperature.diff().fillna(0)
    df['temperature_slope'] = df.groupby('sensor_id').temperature.transform(lambda x: x.rolling(5, min_periods=2).mean().diff()).fillna(0)
    return df

def predict_future(temperatures, horizon=15):
    x = np.asarray(temperatures, dtype=float)
    slope = float(np.mean(np.diff(x[-min(len(x), 10):]))) if len(x) > 1 else 0.0
    return (x[-1] + slope * np.arange(1, horizon + 1)).round(3).tolist()

def risk(prediction, profile='Food'):
    """
    Evaluate temperature excursion risk over future horizon.
    Accurately scales excursion magnitude and alerts on impending breaches.
    """
    lo, hi = PROFILES.get(profile, PROFILES['Generic'])
    p = np.asarray(prediction, dtype=float)
    if len(p) == 0:
        return {
            'risk_score': 0.0,
            'risk_level': 'LOW',
            'risk_reason': f'No forecast points available. Safe profile limits: {lo:.1f} to {hi:.1f} °C.',
            'predicted_breach_time': None
        }
    
    upper_viol = np.maximum(p - hi, 0.0)
    lower_viol = np.maximum(lo - p, 0.0)
    total_viol = upper_viol + lower_viol
    max_viol = float(np.max(total_viol))
    mean_viol = float(np.mean(total_viol))
    diff_mean = float(np.diff(p).mean()) if len(p) > 1 else 0.0
    
    # If any point exceeds safety limits, compute elevated risk
    if max_viol > 0.0:
        base_breach = 25.0
        severity = (max_viol / (hi - lo + 1e-6)) * 50.0 + (mean_viol / (hi - lo + 1e-6)) * 25.0
        trend_term = max(0.0, diff_mean) * 10.0
        score = float(np.clip(base_breach + severity + trend_term, 0.0, 100.0))
    else:
        # Buffer proximity warning (within 0.5 °C of limit)
        buffer = 0.5
        near_hi = np.maximum(p - (hi - buffer), 0.0).mean() / buffer
        near_lo = np.maximum((lo + buffer) - p, 0.0).mean() / buffer
        near_risk = (near_hi + near_lo) * 15.0
        trend_term = max(0.0, diff_mean) * 8.0
        score = float(np.clip(near_risk + trend_term, 0.0, 100.0))
        
    level = 'CRITICAL' if score >= 70.0 else 'HIGH' if score >= 40.0 else 'MEDIUM' if score >= 15.0 else 'LOW'
    breach = next((i + 1 for i, v in enumerate(p) if v < lo or v > hi), None)
    return {
        'risk_score': round(score, 2),
        'risk_level': level,
        'risk_reason': f'Predicted temperature range {p.min():.1f} to {p.max():.1f} °C against {lo:.1f} to {hi:.1f} °C profile limits.',
        'predicted_breach_time': breach
    }
def estimated_power_kw(current: float, ambient: float, intensity: float, duty: float) -> float:
    """Estimated average electrical power demand in kW.
    
    P_base = 0.25 kW (base circulation and electronics)
    P_lift = 0.035 * max(ambient - current, 0) kW (condenser thermal lift penalty)
    P_rated = P_base + P_lift
    P_elec = P_rated * (0.35 + 0.65 * intensity) * duty
    """
    return round(max(0.05, 0.25 + 0.035 * max(ambient - current, 0.0)) * (0.35 + 0.65 * intensity) * duty, 3)

def estimated_energy_kwh(current: float, ambient: float, intensity: float, duty: float, duration_hours: float = 0.25) -> float:
    """Estimated electrical energy in kWh consumed over an operational interval.
    
    E_kwh = P_kw * duration_hours
    For a standard 15-minute control cycle, duration_hours = 15/60 = 0.25 h.
    """
    power_kw = estimated_power_kw(current, ambient, intensity, duty)
    return round(power_kw * duration_hours, 4)

def energy(current: float, ambient: float, intensity: float, duty: float) -> float:
    """Thermodynamic power/energy calculation.
    
    Returns estimated electrical power in kW for compatibility.
    For interval energy in kWh over duration_hours (e.g. 15 min), call estimated_energy_kwh().
    """
    return estimated_power_kw(current, ambient, intensity, duty)

def optimize(current, ambient, future_risk, profile='Food'):
    """Grid-search optimization baseline with thermal infiltration and dual safety limits."""
    lo, hi = PROFILES.get(profile, PROFILES['Generic'])
    ambient_gain = 0.18 * max(ambient - current, 0.0)
    candidates = []
    
    for intensity in np.linspace(0.2, 1.0, 17):
        for duty in np.linspace(0.3, 1.0, 15):
            cooling = 3.2 * intensity * duty
            t_exp = round(current + ambient_gain - cooling, 2)
            upper_viol = max(0.0, t_exp - hi)
            lower_viol = max(0.0, lo - t_exp)
            residual = max(0.0, future_risk - cooling * 8.0) + (upper_viol + lower_viol) * 20.0
            e = energy(current, ambient, intensity, duty)
            is_feasible = (t_exp <= hi) and (t_exp >= lo)
            candidates.append({
                'cooling_intensity': round(float(intensity), 2),
                'compressor_duty_cycle': round(float(duty), 2),
                'safety_risk': round(residual, 2),
                'estimated_energy_kwh': e,
                'expected_temperature': t_exp,
                'feasible': is_feasible
            })
            
    pareto = [
        a for a in candidates
        if not any(
            b['safety_risk'] <= a['safety_risk'] and
            b['estimated_energy_kwh'] <= a['estimated_energy_kwh'] and
            (b['safety_risk'] < a['safety_risk'] or b['estimated_energy_kwh'] < a['estimated_energy_kwh'])
            for b in candidates
        )
    ]
    feasible_pareto = [p for p in pareto if p['feasible']]
    pool = feasible_pareto if feasible_pareto else pareto
    max_e = max(y['estimated_energy_kwh'] for y in pool) if pool else 1.0
    rec = min(pool, key=lambda x: 0.70 * x['safety_risk'] / 100.0 + 0.30 * x['estimated_energy_kwh'] / max_e)
    rec_copy = dict(rec)
    rec_copy['explanation'] = 'Selected from non-dominated energy/safety trade-off with thermal dynamics and safety constraints.'
    return pareto, rec_copy

def prediction_guided_optimization(state, profile='Food'):
    forecast = predict_future(state['temperatures'])
    assessment = risk(forecast, profile)
    pareto, recommendation = optimize(
        state['temperatures'][-1],
        state.get('ambient_temperature', 20),
        assessment['risk_score'],
        profile=profile
    )
    return {
        'forecast': forecast,
        'risk': assessment,
        'pareto_solutions': pareto,
        'recommended_solution': recommendation
    }

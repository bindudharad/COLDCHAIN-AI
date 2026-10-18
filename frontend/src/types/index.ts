export interface Sensor {
  sensor_id: string;
  location: string;
  product_type: string;
  active: boolean;
  reading_count?: number;
  latest_temperature?: number;
  latest_humidity?: number;
  latest_ambient?: number;
  latest_power_kw?: number;
  latest_compressor_state?: boolean;
  latest_door_open?: boolean;
  latest_timestamp?: string;
  temp_min?: number;
  temp_max?: number;
  temp_avg?: number;
}

export interface Reading {
  timestamp: string;
  temperature: number;
  humidity?: number;
  ambient_temperature?: number;
  power_kw?: number;
  compressor_state?: boolean;
  door_open?: boolean;
  data_source?: string;
}

export interface RecommendedSolution {
  cooling_intensity: number;
  compressor_duty_cycle: number;
  estimated_energy_kwh: number;
  predicted_temperature: number;
  predicted_excursion_duration_min: number;
  temperature_difference: number;
  expected_temperature: number;
  feasible?: boolean;
  cooling_pct?: number;
  compressor_pct?: number;
}

export interface RiskAssessment {
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  temperature_trend: string;
  predicted_breach_time: string | null;
  risk_reason: string;
  excursion_probability: number;
  ambient_stress: number;
}

export interface ParetoSolution {
  cooling_intensity: number;
  compressor_duty_cycle: number;
  estimated_energy_kwh: number;
  predicted_temperature: number;
  predicted_excursion_duration_min: number;
  temperature_difference: number;
  expected_temperature: number;
  feasible?: boolean;
}

export interface DecisionData {
  sensor_id: string;
  current_temperature: number;
  current_ambient: number;
  target_range: [number, number];
  product_type: string;
  forecast: number[];
  risk: RiskAssessment;
  recommended_solution: RecommendedSolution;
  pareto_solutions: ParetoSolution[];
  data_provenance: string;
  energy_notice: string;
  reading?: Reading;
}

export interface ModelMetrics {
  mae: number;
  rmse: number;
  r2?: number;
  test_samples?: number;
  training_duration_s?: number;
  window_size?: number;
  horizon?: number;
}

export interface AlertItem {
  id: string;
  severity: string;
  sensor: string;
  message: string;
  resolved: boolean;
}

export interface DatasetItem {
  name: string;
  path: string;
  domain: string;
  source: string;
  provenance: string;
  records: number;
  features: number;
  role: string;
}

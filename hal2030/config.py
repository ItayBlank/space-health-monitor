"""Editable crew, sensor metadata, and demonstration settings.

All people and observations in this project are fictional. These settings are
for a software demonstration, not medical or flight-certified limits.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "telemetry_10min.csv"
DEMO_DURATION = 600
DEMO_SEED = 2030

CREW = [
    {"id": "idan", "name": "Idan", "role": "Mission commander", "sex": "Male", "nationality": "International crew", "portrait": "assets/portraits/idan.png", "accent": "#4DDAC7"},
    {"id": "itay", "name": "Itay", "role": "Flight engineer", "sex": "Male", "nationality": "International crew", "portrait": "assets/portraits/itay.png", "accent": "#7EA9FF"},
    {"id": "anton", "name": "Anton", "role": "Payload specialist", "sex": "Male", "nationality": "International crew", "portrait": "assets/portraits/anton.png", "accent": "#8E9CFF"},
    {"id": "emily", "name": "Emily Carter", "role": "Crew medical officer", "sex": "Female", "nationality": "United States", "portrait": "assets/portraits/emily.png", "accent": "#E4B782"},
    {"id": "sofia", "name": "Sofia Almeida", "role": "Life sciences specialist", "sex": "Female", "nationality": "Brazil", "portrait": "assets/portraits/sofia.png", "accent": "#CA98E8"},
    {"id": "camila", "name": "Camila Santos", "role": "Mission scientist", "sex": "Female", "nationality": "Brazil", "portrait": "assets/portraits/camila.png", "accent": "#FF9AA5"},
]
CREW_BY_ID = {crew["id"]: crew for crew in CREW}

METRICS = {
    "heart_rate": {"label": "Heart rate", "unit": "bpm", "decimals": 0},
    "spo2": {"label": "Blood oxygen", "unit": "%", "decimals": 1},
    "resp_rate": {"label": "Respiration", "unit": "br/min", "decimals": 0},
    "skin_temp": {"label": "Skin temperature", "unit": "°C", "decimals": 1},
    "systolic": {"label": "Systolic pressure", "unit": "mmHg", "decimals": 0},
    "diastolic": {"label": "Diastolic pressure", "unit": "mmHg", "decimals": 0},
    "hrv": {"label": "HRV (RMSSD)", "unit": "ms", "decimals": 0},
    "eeg_alpha": {"label": "EEG alpha power", "unit": "%", "decimals": 1},
    "eeg_beta": {"label": "EEG beta power", "unit": "%", "decimals": 1},
    "motion": {"label": "Motion index", "unit": "a.u.", "decimals": 2},
    "battery": {"label": "Wearable battery", "unit": "%", "decimals": 0},
}

SENSORS = [
    {"id": "ecg", "name": "ECG chest patch", "metrics": ["heart_rate", "hrv"], "placement": "Chest", "sample_rate": "250 Hz raw / 1 Hz demo summary"},
    {"id": "oximeter", "name": "Pulse oximeter", "metrics": ["spo2"], "placement": "Finger / forehead", "sample_rate": "1 Hz summary"},
    {"id": "respiration", "name": "Respiration belt", "metrics": ["resp_rate"], "placement": "Thorax", "sample_rate": "25 Hz raw / 1 Hz demo summary"},
    {"id": "temperature", "name": "Skin temperature patch", "metrics": ["skin_temp"], "placement": "Upper arm", "sample_rate": "1 Hz summary"},
    {"id": "bp", "name": "Blood pressure monitor", "metrics": ["systolic", "diastolic"], "placement": "Upper arm", "sample_rate": "Intermittent real sensor / 1 Hz demo summary"},
    {"id": "eeg", "name": "EEG research headband", "metrics": ["eeg_alpha", "eeg_beta"], "placement": "Head / ear electrodes", "sample_rate": "128 Hz raw / 1 Hz demo summary"},
    {"id": "imu", "name": "Motion tracker", "metrics": ["motion"], "placement": "Wrist", "sample_rate": "50 Hz raw / 1 Hz demo summary"},
]
SENSOR_BY_ID = {sensor["id"]: sensor for sensor in SENSORS}
METRIC_SENSOR = {metric: sensor["id"] for sensor in SENSORS for metric in sensor["metrics"]}

SCENARIOS = [
    {"t": 0, "label": "00:00 · Nominal crew"},
    {"t": 40, "label": "00:40 · Anton: oxygen alert"},
    {"t": 120, "label": "02:00 · Itay: oximeter signal lost"},
    {"t": 185, "label": "03:05 · Emily: exercise / expected response"},
    {"t": 265, "label": "04:25 · Idan: elevated resting vitals"},
    {"t": 355, "label": "05:55 · Sofia: temperature review"},
    {"t": 435, "label": "07:15 · Camila: EEG signal lost"},
    {"t": 530, "label": "08:50 · Crew recovered"},
]

# These are intentionally simple, editable demonstration rules. They are not
# approved NASA thresholds, diagnostic criteria, or individualized baselines.
DEMO_LIMITS = {
    "spo2_critical_low": 90.0,
    "spo2_warning_low": 94.0,
    "heart_rate_critical_high_rest": 130.0,
    "heart_rate_warning_high_rest": 110.0,
    "heart_rate_critical_high_exercise": 180.0,
    "heart_rate_warning_high_exercise": 165.0,
    "heart_rate_critical_low_awake": 40.0,
    "heart_rate_critical_low_asleep": 35.0,
    "resp_rate_critical_high_rest": 28.0,
    "resp_rate_warning_high_rest": 23.0,
    "resp_rate_critical_high_exercise": 42.0,
    "resp_rate_warning_high_exercise": 36.0,
    "resp_rate_critical_low": 7.0,
    "skin_temp_warning_high": 37.0,
    "systolic_critical_high": 180.0,
    "systolic_critical_low": 85.0,
    "systolic_warning_high": 150.0,
    "diastolic_critical_high": 120.0,
    "diastolic_warning_high": 95.0,
}

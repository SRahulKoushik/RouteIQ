import json
import os
from typing import List, Dict, Any

ALERTS_FILE = "alerts.json"
ALERT_THRESHOLD = 7  # Congestion threshold for alert

def load_alerts(filename: str = ALERTS_FILE) -> List[Dict[str, Any]]:
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return json.load(f)

def save_alerts(alerts: List[Dict[str, Any]], filename: str = ALERTS_FILE):
    with open(filename, 'w') as f:
        json.dump(alerts, f)

def add_alert(from_node: str, to_node: str, filename: str = ALERTS_FILE):
    alerts = load_alerts(filename)
    alert = {"from": from_node, "to": to_node}
    if alert not in alerts:
        alerts.append(alert)
        save_alerts(alerts, filename)
        return True
    return False

def remove_alert(from_node: str, to_node: str, filename: str = ALERTS_FILE):
    alerts = load_alerts(filename)
    new_alerts = [a for a in alerts if not (a["from"] == from_node and a["to"] == to_node)]
    save_alerts(new_alerts, filename)
    return len(alerts) != len(new_alerts)

def list_alerts(filename: str = ALERTS_FILE) -> List[Dict[str, Any]]:
    return load_alerts(filename)

def check_alerts(data: List[Dict[str, Any]], filename: str = ALERTS_FILE) -> List[str]:
    """
    Returns a list of alert messages for triggered alerts based on current traffic data.
    """
    alerts = load_alerts(filename)
    triggered = []
    for alert in alerts:
        for segment in data:
            if segment["from"] == alert["from"] and segment["to"] == alert["to"] and segment["weight"] >= ALERT_THRESHOLD:
                triggered.append(f"ALERT: Congestion on {alert['from']} -> {alert['to']} (weight: {segment['weight']})")
    return triggered 
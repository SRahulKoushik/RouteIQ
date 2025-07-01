import json
import os
from typing import List, Dict, Any

HISTORICAL_DATA_FILE = "historical_traffic.json"

def save_traffic_snapshot(data: List[Dict[str, Any]], filename: str = HISTORICAL_DATA_FILE):
    """
    Appends a traffic data snapshot to the historical data file.
    """
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            all_data = json.load(f)
    else:
        all_data = []
    all_data.append(data)
    with open(filename, 'w') as f:
        json.dump(all_data, f)

def load_historical_data(filename: str = HISTORICAL_DATA_FILE) -> List[List[Dict[str, Any]]]:
    """
    Loads all historical traffic data snapshots.
    """
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return json.load(f)

def average_congestion_per_edge(historical_data: List[List[Dict[str, Any]]]) -> Dict[str, float]:
    """
    Computes the average congestion (weight) for each edge across all snapshots.
    Returns a dict: edge_key -> average_weight
    """
    edge_sums = {}
    edge_counts = {}
    for snapshot in historical_data:
        for segment in snapshot:
            edge_key = f"{segment['from']}->{segment['to']}"
            edge_sums[edge_key] = edge_sums.get(edge_key, 0) + segment['weight']
            edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1
    averages = {k: edge_sums[k] / edge_counts[k] for k in edge_sums}
    return averages 
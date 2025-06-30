"""
traffic_api.py: Integration with HERE API for traffic data, with mock fallback.
"""
import requests
from typing import Dict, Any, Tuple, List, Optional
from .graph import Graph
import os
from concurrent.futures import ThreadPoolExecutor

HERE_API_KEY = "YOUR_HERE_API_KEY"  # Replace with your actual HERE API key

# Example: Fetch traffic data from HERE API (mocked for demo)
def fetch_traffic_data(city: str = "Berlin", min_lat: float = None, min_lon: float = None, max_lat: float = None, max_lon: float = None) -> List[Dict[str, Any]]:
    """
    Fetches traffic data from HERE API for a given city or bounding box.
    If bounding box is provided, fetch for that area. Otherwise, use city name.
    Returns a list of road segments with start/end coordinates and congestion level.
    """
    api_key = os.environ.get("HERE_API_KEY", HERE_API_KEY)
    if api_key and api_key != "YOUR_HERE_API_KEY" and min_lat is not None and min_lon is not None and max_lat is not None and max_lon is not None:
        # Use HERE Traffic API for real data
        url = (
            f"https://traffic.ls.hereapi.com/traffic/6.3/flow.json"
            f"?apiKey={api_key}"
            f"&bbox={min_lat},{min_lon};{max_lat},{max_lon}"
            f"&responseattributes=sh,fc"
        )
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            # Parse HERE API response to extract road segments
            segments = []
            for r in data.get("RWS", []):
                for rw in r.get("RW", []):
                    for f in rw.get("FIS", []):
                        for fi in f.get("FI", []):
                            # Each FI is a road segment
                            shape = fi.get("SHP", [])
                            if not shape:
                                continue
                            coords = [tuple(map(float, pt.split(","))) for pt in shape[0].split(" ")]
                            if len(coords) < 2:
                                continue
                            from_pos = coords[0]
                            to_pos = coords[-1]
                            from_id = str(from_pos)
                            to_id = str(to_pos)
                            # Use "CF" (current flow) for congestion/weight
                            weight = fi.get("CF", [{}])[0].get("JF", 1.0)  # JF: Jam Factor (0-10)
                            segments.append({
                                "from": from_id,
                                "to": to_id,
                                "weight": weight,
                                "from_pos": from_pos,
                                "to_pos": to_pos
                            })
            if segments:
                return segments
        except Exception as e:
            print(f"HERE API error: {e}. Falling back to mock data.")
    # Fallback: mock data
    return [
        {"from": "A", "to": "B", "weight": 5, "from_pos": (52.5200, 13.4050), "to_pos": (52.5205, 13.4060)},
        {"from": "B", "to": "C", "weight": 3, "from_pos": (52.5205, 13.4060), "to_pos": (52.5210, 13.4070)},
        {"from": "A", "to": "C", "weight": 10, "from_pos": (52.5200, 13.4050), "to_pos": (52.5210, 13.4070)},
        {"from": "B", "to": "D", "weight": 8, "from_pos": (52.5205, 13.4060), "to_pos": (52.5215, 13.4080)},
        {"from": "C", "to": "D", "weight": 2, "from_pos": (52.5210, 13.4070), "to_pos": (52.5215, 13.4080)},
        {"from": "D", "to": "E", "weight": 4, "from_pos": (52.5215, 13.4080), "to_pos": (52.5220, 13.4090)},
        {"from": "E", "to": "F", "weight": 6, "from_pos": (52.5220, 13.4090), "to_pos": (52.5225, 13.4100)},
        {"from": "C", "to": "F", "weight": 12, "from_pos": (52.5210, 13.4070), "to_pos": (52.5225, 13.4100)},
        {"from": "A", "to": "E", "weight": 15, "from_pos": (52.5200, 13.4050), "to_pos": (52.5220, 13.4090)},
        {"from": "B", "to": "E", "weight": 7, "from_pos": (52.5205, 13.4060), "to_pos": (52.5220, 13.4090)},
    ]

def build_graph_from_traffic(data: List[Dict[str, Any]]) -> Graph:
    """
    Builds a Graph object from traffic data (HERE or mock).
    """
    graph = Graph()
    for segment in data:
        graph.add_node(segment["from"], position=segment["from_pos"])
        graph.add_node(segment["to"], position=segment["to_pos"])
        graph.add_edge(segment["from"], segment["to"], segment["weight"])
    return graph

def fetch_multiple_traffic_data(bboxes, city="Berlin"):
    """
    Fetches traffic data for multiple bounding boxes concurrently using ThreadPoolExecutor.
    Demonstrates I/O-bound concurrency in RouteIQ.
    bboxes: list of (min_lat, min_lon, max_lat, max_lon)
    Returns a list of lists of segments.
    """
    def fetch_one(bbox):
        min_lat, min_lon, max_lat, max_lon = bbox
        return fetch_traffic_data(city, min_lat, min_lon, max_lat, max_lon)
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_one, bboxes))
    return results 
"""
congestion_map.py: Hotspot detection and alternate route logic.
"""
from typing import List, Tuple, Any
from .graph import Graph

CONGESTION_THRESHOLD = 7  # Example threshold for hotspot

def find_hotspots(graph: Graph) -> List[Tuple[Any, Any, float]]:
    """
    Return a list of edges (from, to, weight) that are considered congestion hotspots.
    """
    hotspots = []
    for from_node, neighbors in graph.edges.items():
        for to_node, weight in neighbors:
            if weight >= CONGESTION_THRESHOLD:
                hotspots.append((from_node, to_node, weight))
    return hotspots

def suggest_alternate_path(graph: Graph, start: Any, end: Any) -> Tuple[List[Any], float]:
    """
    Suggest an alternate path avoiding congestion hotspots, if possible.
    """
    # Temporarily remove hotspot edges
    hotspots = find_hotspots(graph)
    removed = []
    for from_node, to_node, weight in hotspots:
        neighbors = graph.edges[from_node]
        for i, (n, w) in enumerate(neighbors):
            if n == to_node and w == weight:
                removed.append((from_node, to_node, weight))
                neighbors.pop(i)
                break
    # Try to find a path
    path, cost = graph.dijkstra(start, end)
    # Restore removed edges
    for from_node, to_node, weight in removed:
        graph.edges[from_node].append((to_node, weight))
    return path, cost 
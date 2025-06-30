"""
graph.py: Graph data structure and pathfinding algorithms (Dijkstra, A*)
"""
from typing import Dict, List, Tuple, Any, Optional, Callable
import heapq
import math

class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges: Dict[Any, List[Tuple[Any, float]]] = {}
        self.positions: Dict[Any, Tuple[float, float]] = {}  # For heuristics (A*)

    def add_node(self, node: Any, position: Optional[Tuple[float, float]] = None):
        self.nodes.add(node)
        if node not in self.edges:
            self.edges[node] = []
        if position:
            self.positions[node] = position

    def add_edge(self, from_node: Any, to_node: Any, weight: float):
        self.edges.setdefault(from_node, []).append((to_node, weight))
        self.edges.setdefault(to_node, [])  # Ensure to_node exists

    def dijkstra(self, start: Any, end: Any) -> Tuple[List[Any], float]:
        queue = [(0, start, [])]
        visited = set()
        while queue:
            (cost, node, path) = heapq.heappop(queue)
            if node in visited:
                continue
            visited.add(node)
            path = path + [node]
            if node == end:
                return path, cost
            for neighbor, weight in self.edges.get(node, []):
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + weight, neighbor, path))
        return [], float('inf')

    def a_star(self, start: Any, end: Any, heuristic: Optional[Callable[[Any, Any], float]] = None) -> Tuple[List[Any], float]:
        if heuristic is None:
            heuristic = self.euclidean_heuristic
        queue = [(0 + heuristic(start, end), 0, start, [])]
        visited = set()
        while queue:
            (est_total, cost, node, path) = heapq.heappop(queue)
            if node in visited:
                continue
            visited.add(node)
            path = path + [node]
            if node == end:
                return path, cost
            for neighbor, weight in self.edges.get(node, []):
                if neighbor not in visited:
                    est = cost + weight + heuristic(neighbor, end)
                    heapq.heappush(queue, (est, cost + weight, neighbor, path))
        return [], float('inf')

    def euclidean_heuristic(self, node1: Any, node2: Any) -> float:
        pos1 = self.positions.get(node1)
        pos2 = self.positions.get(node2)
        if pos1 and pos2:
            return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])
        return 0.0

    def nearest_node(self, lat: float, lon: float) -> Any:
        """
        Finds the node in the graph whose position is closest to the given (lat, lon).
        Returns the node ID.
        """
        min_dist = float('inf')
        nearest = None
        for node, pos in self.positions.items():
            dist = math.hypot(pos[0] - lat, pos[1] - lon)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest 
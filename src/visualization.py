import folium
from typing import List, Tuple, Any


def plot_route_map(graph, route: List[Any], hotspots: List[Tuple[Any, Any, float]], filename: str = "route_map.html"):
    """
    Plots the graph, highlights the route, and marks congestion hotspots on a Folium map.
    """
    # Get all node positions
    positions = graph.positions
    # Center map on the first node in the route or arbitrary node
    if route and route[0] in positions:
        center = positions[route[0]]
    elif positions:
        center = next(iter(positions.values()))
    else:
        center = (0, 0)
    m = folium.Map(location=center, zoom_start=14)

    # Draw all edges
    for from_node, neighbors in graph.edges.items():
        for to_node, weight in neighbors:
            if from_node in positions and to_node in positions:
                folium.PolyLine([positions[from_node], positions[to_node]], color='gray', weight=2, opacity=0.5).add_to(m)

    # Highlight the route
    if route:
        route_coords = [positions[node] for node in route if node in positions]
        folium.PolyLine(route_coords, color='blue', weight=5, opacity=0.8, tooltip='Route').add_to(m)
        # Mark start and end
        if route_coords:
            folium.Marker(route_coords[0], popup='Start', icon=folium.Icon(color='green')).add_to(m)
            folium.Marker(route_coords[-1], popup='End', icon=folium.Icon(color='red')).add_to(m)

    # Mark congestion hotspots
    for from_node, to_node, weight in hotspots:
        if from_node in positions and to_node in positions:
            folium.PolyLine([positions[from_node], positions[to_node]], color='red', weight=4, opacity=0.7, tooltip=f'Hotspot (weight: {weight})').add_to(m)

    m.save(filename)
    print(f"Map saved to {filename}. Open it in your browser to view.") 
"""
cli.py: Command-line interface for RouteIQ
"""
import argparse
from .traffic_api import fetch_traffic_data, build_graph_from_traffic
from .congestion_map import find_hotspots, suggest_alternate_path
from .graph import Graph
import threading
import time
import timeit


def poll_traffic(graph, city, min_lat=None, min_lon=None, max_lat=None, max_lon=None, interval=60):
    """
    Periodically updates the graph's edge weights from the HERE API (or mock).
    Runs in a background daemon thread to simulate live traffic updates.
    """
    while True:
        data = fetch_traffic_data(city, min_lat, min_lon, max_lat, max_lon)
        # Update weights in the existing graph
        for segment in data:
            from_node = segment["from"]
            to_node = segment["to"]
            weight = segment["weight"]
            # Update the edge if it exists
            if from_node in graph.edges:
                for i, (neighbor, _) in enumerate(graph.edges[from_node]):
                    if neighbor == to_node:
                        graph.edges[from_node][i] = (to_node, weight)
        time.sleep(interval)


def main():
    """
    Main CLI entrypoint for RouteIQ.
    Supports:
    - Node ID or coordinate input
    - Background traffic polling (multithreading)
    - Parallel pathfinding (multithreading)
    """
    parser = argparse.ArgumentParser(description="RouteIQ: Find the shortest, least-congested path in a city.")
    parser.add_argument("--from", dest="start", help="Start location (node id)")
    parser.add_argument("--to", dest="end", help="End location (node id)")
    parser.add_argument("--from-lat", type=float, help="Start latitude (alternative to --from)")
    parser.add_argument("--from-lon", type=float, help="Start longitude (alternative to --from)")
    parser.add_argument("--to-lat", type=float, help="End latitude (alternative to --to)")
    parser.add_argument("--to-lon", type=float, help="End longitude (alternative to --to)")
    parser.add_argument("--algorithm", choices=["dijkstra", "astar"], default="dijkstra", help="Pathfinding algorithm")
    parser.add_argument("--avoid-hotspots", action="store_true", help="Avoid congestion hotspots if possible")
    parser.add_argument("--city", default="Berlin", help="City name (for HERE API)")
    parser.add_argument("--poll-interval", type=int, default=60, help="Traffic polling interval in seconds (default: 60)")
    parser.add_argument("--compare-algorithms", action="store_true", help="Compare Dijkstra and A* in parallel threads")
    args = parser.parse_args()

    # Determine start and end nodes
    if args.from_lat is not None and args.from_lon is not None and args.to_lat is not None and args.to_lon is not None:
        # Compute bounding box for HERE API
        min_lat = min(args.from_lat, args.to_lat)
        max_lat = max(args.from_lat, args.to_lat)
        min_lon = min(args.from_lon, args.to_lon)
        max_lon = max(args.from_lon, args.to_lon)
        data = fetch_traffic_data(args.city, min_lat, min_lon, max_lat, max_lon)
        graph = build_graph_from_traffic(data)
        # Start background polling thread
        poll_thread = threading.Thread(target=poll_traffic, args=(graph, args.city, min_lat, min_lon, max_lat, max_lon, args.poll_interval), daemon=True)
        poll_thread.start()
        start_node = graph.nearest_node(args.from_lat, args.from_lon)
        end_node = graph.nearest_node(args.to_lat, args.to_lon)
        if start_node is None or end_node is None:
            print("Could not find nearest nodes for the provided coordinates.")
            return
    elif args.start is not None and args.end is not None:
        data = fetch_traffic_data(args.city)
        graph = build_graph_from_traffic(data)
        # Start background polling thread (city-wide)
        poll_thread = threading.Thread(target=poll_traffic, args=(graph, args.city, None, None, None, None, args.poll_interval), daemon=True)
        poll_thread.start()
        start_node = args.start
        end_node = args.end
    else:
        print("You must provide either --from and --to (node IDs) or --from-lat, --from-lon, --to-lat, --to-lon (coordinates).")
        return

    def run_dijkstra():
        """Run Dijkstra's algorithm and record timing (for parallel comparison)."""
        start = timeit.default_timer()
        path, cost = graph.dijkstra(start_node, end_node)
        elapsed = timeit.default_timer() - start
        results['dijkstra'] = (path, cost, elapsed)

    def run_astar():
        """Run A* algorithm and record timing (for parallel comparison)."""
        start = timeit.default_timer()
        path, cost = graph.a_star(start_node, end_node)
        elapsed = timeit.default_timer() - start
        results['astar'] = (path, cost, elapsed)

    results = {}

    if args.compare_algorithms:
        # Run both algorithms in parallel threads for concurrency demonstration
        t1 = threading.Thread(target=run_dijkstra)
        t2 = threading.Thread(target=run_astar)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print("\n--- Parallel Pathfinding Results ---")
        d_path, d_cost, d_time = results['dijkstra']
        a_path, a_cost, a_time = results['astar']
        print(f"Dijkstra: Path: {' -> '.join(d_path)}, Cost: {d_cost}, Time: {d_time:.4f}s")
        print(f"A*:      Path: {' -> '.join(a_path)}, Cost: {a_cost}, Time: {a_time:.4f}s")
    else:
        if args.avoid_hotspots:
            path, cost = suggest_alternate_path(graph, start_node, end_node)
            if not path:
                print("No alternate path found avoiding hotspots. Showing best available route.")
                path, cost = getattr(graph, args.algorithm)(start_node, end_node)
        else:
            path, cost = getattr(graph, args.algorithm)(start_node, end_node)

        print(f"Path: {' -> '.join(path)}")
        print(f"Total cost: {cost}")
        hotspots = find_hotspots(graph)
        if hotspots:
            print("Congestion hotspots:")
            for from_node, to_node, weight in hotspots:
                print(f"  {from_node} -> {to_node} (weight: {weight})")
        else:
            print("No congestion hotspots detected.") 
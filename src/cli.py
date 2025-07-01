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
    parser.add_argument("--visualize", action="store_true", help="Visualize the route and congestion hotspots on a map")
    parser.add_argument("--record-snapshot", action="store_true", help="Record a snapshot of current traffic data for historical analysis")
    parser.add_argument("--historical-report", action="store_true", help="Show average congestion per edge from historical data")
    parser.add_argument("--add-alert", nargs=2, metavar=("FROM", "TO"), help="Add an alert for congestion on a specific edge (FROM TO)")
    parser.add_argument("--remove-alert", nargs=2, metavar=("FROM", "TO"), help="Remove an alert for a specific edge (FROM TO)")
    parser.add_argument("--list-alerts", action="store_true", help="List all registered congestion alerts")
    parser.add_argument("--mode", choices=["car", "bike", "public"], default="car", help="Transport mode: car, bike, or public (default: car)")
    args = parser.parse_args()

    # Determine start and end nodes
    if args.from_lat is not None and args.from_lon is not None and args.to_lat is not None and args.to_lon is not None:
        # Compute bounding box for HERE API
        min_lat = min(args.from_lat, args.to_lat)
        max_lat = max(args.from_lat, args.to_lat)
        min_lon = min(args.from_lon, args.to_lon)
        max_lon = max(args.from_lon, args.to_lon)
        data = fetch_traffic_data(args.city, min_lat, min_lon, max_lat, max_lon)
        graph = build_graph_from_traffic(data, mode=args.mode)
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
        graph = build_graph_from_traffic(data, mode=args.mode)
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
        # Visualization
        if args.visualize:
            try:
                from .visualization import plot_route_map
                plot_route_map(graph, path, hotspots)
            except ImportError:
                print("Visualization requires the 'folium' package. Please install it with 'pip install folium'.")

    # After graph is built, before/after route computation
    if args.record_snapshot:
        try:
            from .historical_traffic import save_traffic_snapshot
            save_traffic_snapshot(data)
            print("Traffic snapshot recorded.")
        except ImportError:
            print("Snapshot recording requires the 'historical_traffic' module.")

    # Historical report (can be run standalone)
    if args.historical_report:
        try:
            from .historical_traffic import load_historical_data, average_congestion_per_edge
            historical_data = load_historical_data()
            if not historical_data:
                print("No historical data found.")
            else:
                averages = average_congestion_per_edge(historical_data)
                print("Average congestion per edge (historical):")
                for edge, avg in averages.items():
                    print(f"  {edge}: {avg:.2f}")
        except ImportError:
            print("Historical analysis requires the 'historical_traffic' module.")
        return

    # Alert management (standalone)
    if args.add_alert:
        from_node, to_node = args.add_alert
        try:
            from .alerts import add_alert
            if add_alert(from_node, to_node):
                print(f"Alert added for {from_node} -> {to_node}.")
            else:
                print(f"Alert for {from_node} -> {to_node} already exists.")
        except ImportError:
            print("Alert management requires the 'alerts' module.")
        return
    if args.remove_alert:
        from_node, to_node = args.remove_alert
        try:
            from .alerts import remove_alert
            if remove_alert(from_node, to_node):
                print(f"Alert removed for {from_node} -> {to_node}.")
            else:
                print(f"No alert found for {from_node} -> {to_node}.")
        except ImportError:
            print("Alert management requires the 'alerts' module.")
        return
    if args.list_alerts:
        try:
            from .alerts import list_alerts
            alerts = list_alerts()
            if not alerts:
                print("No alerts registered.")
            else:
                print("Registered alerts:")
                for alert in alerts:
                    print(f"  {alert['from']} -> {alert['to']}")
        except ImportError:
            print("Alert management requires the 'alerts' module.")
        return

    # After fetching traffic data, check for triggered alerts
    try:
        from .alerts import check_alerts
        alert_msgs = check_alerts(data)
        for msg in alert_msgs:
            print(msg)
    except ImportError:
        pass 
# RouteIQ

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)  
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**RouteIQ** is a modular Python CLI tool that models a city's traffic network using graphs and finds the shortest, least-congested path between two points using Dijkstra's and A* algorithms. It integrates with the HERE API for real-time or simulated traffic data.

---

## 🚦 Features
- Graph-based city traffic modeling
- Shortest path search (Dijkstra & A*)
- Realistic traffic data (HERE API or mock)
- Congestion hotspot detection & avoidance
- **Route visualization on interactive map** (`--visualize`)
- **Historical traffic analysis** (record and report with `--record-snapshot`, `--historical-report`)
- **Congestion alerts** (add, remove, and list with `--add-alert`, `--remove-alert`, `--list-alerts`)
- **Multi-modal routing** (car, bike, public transport with `--mode`)
- CLI interface: `python main.py --from X --to Y`
- Modular, extensible codebase

## 📦 Installation
```bash
# Clone the repo
$ git clone https://github.com/SRahulKoushik/RouteIQ.git
$ cd RouteIQ

# (Optional) Create and activate a virtual environment
$ python -m venv venv
# On Windows:
$ venv/Scripts/activate
# On macOS/Linux:
$ source venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt
```

## 🚀 Usage
```bash
python main.py --from A --to D --algorithm astar --avoid-hotspots
python main.py --from-lat 52.5200 --from-lon 13.4050 --to-lat 52.5210 --to-lon 13.4070 --algorithm astar
python main.py --from-lat 52.5200 --from-lon 13.4050 --to-lat 52.5210 --to-lon 13.4070 --compare-algorithms
python main.py --from A --to D --visualize
python main.py --from A --to D --mode bike
python main.py --from A --to D --mode public
python main.py --from A --to D --record-snapshot
python main.py --historical-report
python main.py --add-alert A B
python main.py --remove-alert A B
python main.py --list-alerts
```

- `--from`, `--to`: Start and end node IDs
- `--algorithm`: `dijkstra` (default) or `astar`
- `--avoid-hotspots`: Try to avoid congestion
- `--city`: City name (for HERE API)
- `--compare-algorithms`: Run Dijkstra and A* in parallel and compare results.
- `--poll-interval`: Set background traffic polling interval (default: 60s).
- `--visualize`: Show the computed route and hotspots on an interactive map
- `--mode`: Transport mode (`car`, `bike`, `public`)
- `--record-snapshot`: Record a snapshot of current traffic data for historical analysis
- `--historical-report`: Show average congestion per edge from historical data
- `--add-alert FROM TO`: Add an alert for congestion on a specific edge
- `--remove-alert FROM TO`: Remove an alert for a specific edge
- `--list-alerts`: List all registered congestion alerts

## 🗺️ Example
```
Path: A -> B -> C -> D
Total cost: 10
Congestion hotspots:
  B -> D (weight: 8)
```

## 🔗 HERE API
- [HERE Traffic API](https://developer.here.com/documentation/traffic-api/dev_guide/index.html)
- Replace `YOUR_HERE_API_KEY` in `traffic_api.py` with your API key.

## 🧪 Mock Data vs Real Data

RouteIQ works out-of-the-box with built-in mock data, so you can demo all features without any setup. If you want to use real traffic data, simply provide your HERE API key.

- **Mock Data (default):**
  - If no HERE API key is set, RouteIQ uses a small, hardcoded city network for all routefinding and concurrency features.
  - Great for demos, development, and testing.
  - Example:
    ```bash
    python main.py --from A --to F --compare-algorithms
    python main.py --from-lat 52.5200 --from-lon 13.4050 --to-lat 52.5225 --to-lon 13.4100
    ```

- **Real Data (optional):**
  - To use real traffic data, set your HERE API key as an environment variable:
    ```bash
    export HERE_API_KEY=your_actual_api_key
    ```
    Or edit `src/traffic_api.py` and replace `"YOUR_HERE_API_KEY"` with your key.
  - Use coordinates within a real city for best results.
  - Example:
    ```bash
    python main.py --from-lat 52.5200 --from-lon 13.4050 --to-lat 52.5225 --to-lon 13.4100
    ```

If the API key is missing or invalid, RouteIQ will automatically fall back to mock data.

## 🤝 Contributing
Pull requests are welcome! For major changes, open an issue first to discuss what you would like to change.

---

## 📄 License
MIT 

## ⚡️ Concurrency & Multithreading
RouteIQ demonstrates Python concurrency and multithreading:
- **Parallel pathfinding:** Use `--compare-algorithms` to run Dijkstra and A* in parallel threads and compare results in real time.
- **Background traffic polling:** The graph updates live in the background using a daemon thread (see `--poll-interval`).
- **Concurrent HERE API calls:** Fetch traffic data for multiple areas in parallel using `ThreadPoolExecutor` (see `fetch_multiple_traffic_data` in `traffic_api.py`). 
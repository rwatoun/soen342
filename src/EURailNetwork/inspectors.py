from collections import Counter
from typing import Iterable
from .models import Connection
from .registries import RailNetwork

# these are the called methods upon the user's cli commands which fetches the data from all the created classes/registries

def print_summary(net: RailNetwork, top: int = 5) -> None:
    print(f"Cities: {len(net.cities.items)} | Trains: {len(net.trains.items)} | Connections: {len(net.connections)}")
    by_dep = Counter(c.dep_city.name for c in net.connections).most_common(top)
    by_arr = Counter(c.arr_city.name for c in net.connections).most_common(top)
    by_train = Counter(c.train.name for c in net.connections).most_common(top)
    print("\nTop departure cities:", by_dep)
    print("Top arrival cities:   ", by_arr)
    print("Top trains:           ", by_train)

def print_city(net: RailNetwork, name: str, limit: int = 10) -> None:
    city = next((c for c in net.cities.items if c.name == name), None)
    if not city: 
        print(f"City '{name}' not found"); return
    print(f"{city.name}: {len(city.departures)} departures, {len(city.arrivals)} arrivals")
    for c in city.departures[:limit]:
        print(f"  DEP {c.route_id}: {c.dep_time} → {c.arr_city.name} ({c.trip_minutes} min) [{c.train.name}]")
    for c in city.arrivals[:limit]:
        print(f"  ARR {c.route_id}: {c.arr_city.name} ← {c.dep_city.name} {c.arr_time} [{c.train.name}]")

def print_train(net: RailNetwork, name: str, limit: int = 10) -> None:
    train = next((t for t in net.trains.items if t.name == name), None)
    if not train:
        print(f"Train '{name}' not found"); return
    print(f"{train.name}: {len(train.connections)} connections")
    for c in train.connections[:limit]:
        print(f"  {c.route_id}: {c.dep_city.name} {c.dep_time} → {c.arr_city.name} {c.arr_time} ({c.trip_minutes} min)")

def check_invariants(net: RailNetwork) -> None:
    """Assert the graph is wired correctly."""
    n = len(net.connections)
    assert n == sum(len(c.departures) for c in net.cities.items),  "Mismatch: sum(city.departures) != connections"
    assert n == sum(len(c.arrivals)   for c in net.cities.items),  "Mismatch: sum(city.arrivals)   != connections"
    assert n == sum(len(t.connections) for t in net.trains.items), "Mismatch: sum(train.connections)!= connections"
    # back-links
    for c in net.connections:
        assert c in c.dep_city.departures, "Connection missing from dep_city.departures"
        assert c in c.arr_city.arrivals,   "Connection missing from arr_city.arrivals"
        assert c in c.train.connections,   "Connection missing from train.connections"
    print("invariants OK")

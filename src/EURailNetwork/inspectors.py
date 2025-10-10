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

def print_connection_search_results(connections: list[Connection],
                                    sort_by: str = None,
                                    ascending: bool = True) -> None:
    
    # Case where there are no connections that can be retrieved and that match the criteria given by the client
    if not connections:
        print("No connections found matching the parameters given.")
        return

    # Sorting information
    order_str = "ascending" if ascending else "descending"
    sort_info = f" (sorted by {sort_by} {order_str})" if sort_by else ""

    # Displaying number of connections found matching criteria
    print(f"\nFound {len(connections)} connections{sort_info}.\n")
    
    # Displaying matched connections
    for i, c in enumerate(connections, 1):
        # Converting days set to readable format
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        operating_days = ", ".join(day_names[day] for day in sorted(c.days))
        
        # Convert duration to readable format - X h Y m
        duration_str = f"{c.trip_minutes//60}h{c.trip_minutes%60:02d}m"
        
        print(f"CONNECTION #{i}")
        print(f"  From:          {c.dep_city.name}")
        print(f"  To:            {c.arr_city.name}") 
        print(f"  Departure:     {c.dep_time.strftime('%H:%M')}")
        print(f"  Arrival:       {c.arr_time.strftime('%H:%M')}")
        print(f"  Duration:      {duration_str} ({c.trip_minutes} minutes)")
        print(f"  Train:         {c.train.name}")
        print(f"  Operating:     {operating_days}")
        print(f"  1st Class:     {c.first_class_eur}€")
        print(f"  2nd Class:     {c.second_class_eur}€")

def print_indirect_connection_results(routes: list[dict]):
    """Display multi-leg routes with total and waiting times."""
    if not routes:
        print("No indirect routes found.")
        return

    print(f"\nFound {len(routes)} indirect route(s):\n")
    for i, r in enumerate(routes, 1):
        segs = " → ".join(seg.dep_city.name for seg in r["segments"]) \
               + f" → {r['segments'][-1].arr_city.name}"
        hours, mins = divmod(r["total_minutes"], 60)
        print(f"ROUTE #{i}: {segs}")
        print(f"  Total Duration: {hours}h{mins:02d}m "
              f"(includes {r['wait_minutes']} min waiting)")
        print("  Segments:")
        for s in r["segments"]:
            print(f"    {s.dep_city.name} {s.dep_time.strftime('%H:%M')} → "
                  f"{s.arr_city.name} {s.arr_time.strftime('%H:%M')} "
                  f"[{s.train.name}] ({s.trip_minutes} min)")
        print()
        
def print_indirect_connection_results(routes):
    if not routes:
        print("No indirect routes found.")
        return

    print(f"\nFound {len(routes)} indirect route(s):\n")
    for idx, route in enumerate(routes, start=1):
        segs = route["segments"]
        total = route["total_minutes"]
        print(f"ROUTE #{idx}: {segs[0].dep_city.name} → {segs[-1].arr_city.name}")
        print(f"  Total Duration: {total // 60}h{total % 60:02d}m")
        print("  Segments:")
        for i, seg in enumerate(segs):
            print(f"    {seg.dep_city.name} {seg.dep_time.strftime('%H:%M')} → {seg.arr_city.name} {seg.arr_time.strftime('%H:%M')} [{seg.train.name}] ({seg.trip_minutes} min)")
            if i < len(segs) - 1:
                print(f"    Time to change connection in {seg.arr_city.name}: {route['wait_times'][i]} minutes")
        print()


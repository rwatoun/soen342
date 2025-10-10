from collections import Counter
from typing import Iterable
from .models import Connection
from .registries import RailNetwork
from .registries import norm_name
from colorama import Fore, Style
from .registries import norm_name


# these are the called methods upon the user's cli commands which fetches the data from all the created classes/registries

def print_summary(net: RailNetwork, top: int = 5) -> None:
    print(f"Cities: {len(net.cities.items)} | Trains: {len(net.trains.items)} | Connections: {len(net.connections)}")
    by_dep = Counter(c.dep_city.name for c in net.connections).most_common(top)
    by_arr = Counter(c.arr_city.name for c in net.connections).most_common(top)
    by_train = Counter(c.train.name for c in net.connections).most_common(top)
    print("\nTop departure cities:", by_dep)
    print("Top arrival cities:   ", by_arr)
    print("Top trains:           ", by_train)

def print_city(g, city_name, limit=10):
    """Display information about a city (case-insensitive)."""
    normalized_target = norm_name(city_name)
    found_city = None

    # match normalized name
    for c in g.cities.items:
        if norm_name(c.name) == normalized_target:
            found_city = c
            break

    if not found_city:
        print(Fore.RED + f"City '{city_name}' not found" + Style.RESET_ALL)
        return

    print(Fore.CYAN + f"\nCity: {found_city.name}" + Style.RESET_ALL)
    print(Fore.LIGHTBLACK_EX + "----------------------------------" + Style.RESET_ALL)
    print(Fore.GREEN + f"Departures ({len(found_city.departures)}):" + Style.RESET_ALL)

    for conn in found_city.departures[:limit]:
        print(f"  {conn.dep_time.strftime('%H:%M')} → {conn.arr_city.name:<15} [{conn.train.name}] "
              f"({conn.trip_minutes} min) — {conn.second_class_eur}€ 2nd | {conn.first_class_eur}€ 1st")

    print(Fore.GREEN + f"\nArrivals ({len(found_city.arrivals)}):" + Style.RESET_ALL)
    for conn in found_city.arrivals[:limit]:
        print(f"  {conn.arr_time.strftime('%H:%M')} ← {conn.dep_city.name:<15} [{conn.train.name}] "
              f"({conn.trip_minutes} min) — {conn.second_class_eur}€ 2nd | {conn.first_class_eur}€ 1st")

    print()

def print_train(g, train_name, limit=10):
    """Display information about a train (case-insensitive)."""
    normalized_target = norm_name(train_name)
    found_train = None

    # Find train regardless of case or accents
    for t in g.trains.items:
        if norm_name(t.name) == normalized_target:
            found_train = t
            break

    if not found_train:
        print(Fore.RED + f"Train '{train_name}' not found" + Style.RESET_ALL)
        return

    print(Fore.CYAN + f"\nTrain: {found_train.name}" + Style.RESET_ALL)
    print(Fore.LIGHTBLACK_EX + "----------------------------------" + Style.RESET_ALL)

    for conn in found_train.connections[:limit]:
        print(f"{conn.dep_city.name:<15} {conn.dep_time.strftime('%H:%M')} → "
              f"{conn.arr_city.name:<15} {conn.arr_time.strftime('%H:%M')} "
              f"({conn.trip_minutes} min) — {conn.second_class_eur}€ 2nd | {conn.first_class_eur}€ 1st")

    print()


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
    """Print formatted search results, showing sorting info and price/duration/time clearly."""

    if not connections:
        print("No connections found matching the parameters given.")
        return

    # Sorting info
    order_str = "ascending" if ascending else "descending"
    sort_label = sort_by.replace("_", " ").title() if sort_by else "unspecified"
    print(f"\nFound {len(connections)} connections (sorted by {sort_label} {order_str}).\n")

    for i, c in enumerate(connections, 1):
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        operating_days = ", ".join(day_names[d] for d in sorted(c.days))

        
        duration_str = f"{c.trip_minutes // 60}h{c.trip_minutes % 60:02d}m"

        
        print(f"CONNECTION #{i}")
        print(f"  From:          {c.dep_city.name}")
        print(f"  To:            {c.arr_city.name}")
        print(f"  Departure:     {c.dep_time.strftime('%H:%M')}")
        print(f"  Arrival:       {c.arr_time.strftime('%H:%M')}")
        print(f"  Duration:      {duration_str} ({c.trip_minutes} minutes)")
        print(f"  Train:         {c.train.name}")
        print(f"  Operating:     {operating_days}")
        print(f"  1st Class:     {c.first_class_eur:>3}€")
        print(f"  2nd Class:     {c.second_class_eur:>3}€")

        if sort_by in ["first_class_eur", "second_class_eur"]:
            print(f"  → Sorted by:   {sort_label} ({'lowest' if ascending else 'highest'} first)")
        elif sort_by in ["dep_time", "arr_time"]:
            print(f"  → Sorted by:   {sort_label} ({'earliest' if ascending else 'latest'} first)")
        elif sort_by == "trip_minutes":
            print(f"  → Sorted by:   Duration ({'shortest' if ascending else 'longest'} first)")
        print()


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


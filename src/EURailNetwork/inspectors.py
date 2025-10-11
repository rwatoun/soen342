from collections import Counter
from typing import Iterable
from .models import Connection
from .registries import RailNetwork, norm_name
from colorama import Fore, Style


# these are the called methods upon the user's cli commands which fetches the data from all the created classes/registries
def print_summary(net: RailNetwork, top: int = 1200) -> None:
    print(Fore.MAGENTA + "\n=== NETWORK SUMMARY ===" + Style.RESET_ALL)
    print(Fore.LIGHTBLACK_EX +
          f"Cities: {len(net.cities.items)} | "
          f"Trains: {len(net.trains.items)} | "
          f"Connections: {len(net.connections)}"
          + Style.RESET_ALL)

    # Departure cities
    dep_counts = Counter(c.dep_city.name for c in net.connections)
    print(Fore.CYAN + "\nDEPARTURE CITIES" + Style.RESET_ALL)
    print(Fore.WHITE + f"Total: {len(dep_counts)} cities\n" + Style.RESET_ALL)
    print(", ".join(f"{Fore.YELLOW}{city}{Style.RESET_ALL} ({count})" for city, count in dep_counts.most_common()))

    # Arrival cities
    arr_counts = Counter(c.arr_city.name for c in net.connections)
    print(Fore.CYAN + "\nARRIVAL CITIES" + Style.RESET_ALL)
    print(Fore.WHITE + f"Total: {len(arr_counts)} cities\n" + Style.RESET_ALL)
    print(", ".join(f"{Fore.YELLOW}{city}{Style.RESET_ALL} ({count})" for city, count in arr_counts.most_common()))

    # Trains
    train_counts = Counter(c.train.name for c in net.connections)
    print(Fore.CYAN + "\nTRAINS" + Style.RESET_ALL)
    print(Fore.WHITE + f"Total: {len(train_counts)} train types\n" + Style.RESET_ALL)
    print(", ".join(f"{Fore.YELLOW}{name}{Style.RESET_ALL} ({count})" for name, count in train_counts.most_common()))

    print(Fore.LIGHTBLACK_EX + "\n---------------------------------------------\n" + Style.RESET_ALL)

def print_city(g, city_name, limit=10):
    """Display information about a city (case-insensitive, supports substrings)."""
    normalized_target = norm_name(city_name)
    found_city = None

    
    for c in g.cities.items:
        if normalized_target in norm_name(c.name):
            found_city = c
            break

    if not found_city:
        print(Fore.RED + f"No city found matching '{city_name}'" + Style.RESET_ALL)
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
    """Display information about a train (case-insensitive, supports partial match)."""
    normalized_target = norm_name(train_name)
    found_train = None

    # Match by substring (partial)
    for t in g.trains.items:
        if normalized_target in norm_name(t.name):
            found_train = t
            break

    if not found_train:
        print(Fore.RED + f"No train found matching '{train_name}'" + Style.RESET_ALL)
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
    """Print formatted search results."""
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
        print(f"  1st Class:     {c.first_class_eur}€")
        print(f"  2nd Class:     {c.second_class_eur}€")

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
    for idx, route in enumerate(routes, start=1):
        segs = route["segments"]
        total = route["total_minutes"]
        print(f"ROUTE #{idx}: {segs[0].dep_city.name} → {segs[-1].arr_city.name}")
        print(f"  Total Duration: {total // 60}h{total % 60:02d}m")
        print("  Segments:")
        for i, seg in enumerate(segs):
            print(f"    {seg.dep_city.name} {seg.dep_time.strftime('%H:%M')} → "
                  f"{seg.arr_city.name} {seg.arr_time.strftime('%H:%M')} [{seg.train.name}] ({seg.trip_minutes} min)")
            if i < len(segs) - 1:
                print(f"    Time to change connection in {seg.arr_city.name}: {route['wait_times'][i]} minutes")
        print()

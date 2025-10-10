import argparse
from .loader import read_raw_csv, build_network_from_df
from .inspectors import (
    print_summary,
    print_city,
    print_train,
    print_connection_search_results,
)
from .utils_time import parse_time


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")

    # Option in flag if you want to show a specific number of rows
    p.add_argument("--head", type=int, default=5, help="Number of connections to preview")

    # Top-level actions
    p.add_argument("--summary", action="store_true")
    p.add_argument("--city")
    p.add_argument("--train")

    # Connection search arguments
    p.add_argument("--search-connections", action="store_true",
                   help="Search for connections using any parameters")

    # City search filters
    p.add_argument("--from", dest="from_city", help="Departure city")
    p.add_argument("--to", dest="to_city", help="Arrival city")

    # Train type search filters
    p.add_argument("--train-type", help="Train type (substring match)")

    # First class price filters
    p.add_argument("--min-first-price", type=int, help="Minimum first class price")
    p.add_argument("--max-first-price", type=int, help="Maximum first class price")

    # Second class price filters
    p.add_argument("--min-second-price", type=int, help="Minimum second class price")
    p.add_argument("--max-second-price", type=int, help="Maximum second class price")

    # Departure time filters
    p.add_argument("--dep-time-start", help="Earliest departure time (HH:MM)")
    p.add_argument("--dep-time-end", help="Latest departure time (HH:MM)")

    # Arrival time filters
    p.add_argument("--arr-time-start", help="Earliest arrival time (HH:MM)")
    p.add_argument("--arr-time-end", help="Latest arrival time (HH:MM)")

    # Duration filters
    p.add_argument("--min-duration", type=int, help="Minimum trip duration (minutes)")
    p.add_argument("--max-duration", type=int, help="Maximum trip duration (minutes)")

    # Day of the week filter
    p.add_argument("--weekday", type=int, choices=range(7),
                   help="Weekday (0=Monday, 6=Sunday)")

    # Sorting
    p.add_argument(
        "--sort-by",
        choices=[
            "dep_time", "arr_time", "trip_minutes", "first_class_eur",
            "second_class_eur", "dep_city", "arr_city", "train_name",
        ],
        default="dep_time",
        help="Sort results by one of the available parameters",
    )
    p.add_argument("--order", choices=["asc", "desc"], default="asc",
                   help="Sort order: asc (ascending) or desc (descending)")

    # Parse arguments
    args = p.parse_args()

    # Build network from CSV
    df = read_raw_csv(args.csv_path)
    g = build_network_from_df(df)

    # === CONNECTION SEARCH MODE ===
    if args.search_connections:
        dep_start = parse_time(args.dep_time_start) if args.dep_time_start else None
        dep_end = parse_time(args.dep_time_end) if args.dep_time_end else None
        arr_start = parse_time(args.arr_time_start) if args.arr_time_start else None
        arr_end = parse_time(args.arr_time_end) if args.arr_time_end else None

        ascending = (args.order == "asc")

        # Perform connection search (direct)
        connections = g.search_connections(
            depart_city=args.from_city,
            arrival_city=args.to_city,
            train_type=args.train_type,
            min_first_class_price=args.min_first_price,
            max_first_class_price=args.max_first_price,
            min_second_class_price=args.min_second_price,
            max_second_class_price=args.max_second_price,
            min_departure_time=dep_start,
            max_departure_time=dep_end,
            min_arrival_time=arr_start,
            max_arrival_time=arr_end,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            weekday=args.weekday,
            sort_by=args.sort_by,
            ascending=ascending,
        )

        if connections:
            print_connection_search_results(connections, args.sort_by, ascending)
        else:
            print("No direct connections found — searching for indirect routes...\n")
            routes = g.find_indirect_connections(args.from_city, args.to_city)

            if not routes or len(routes) == 0:
                print("No indirect routes found.")
            else:
                routes.sort(key=lambda r: r["total_minutes"])

                print(f"Found {len(routes)} indirect route(s):\n")
                for i, route in enumerate(routes, 1):
                    total_h, total_m = divmod(route["total_minutes"], 60)
                    print(f"ROUTE #{i}:")
                    print(f"  Total Duration: {total_h}h{total_m:02d}m")

                    for idx, seg in enumerate(route["segments"]):
                        print(f"    {seg.dep_city.name:>10} {seg.dep_time.strftime('%H:%M')} → "
                              f"{seg.arr_city.name:<15} {seg.arr_time.strftime('%H:%M')} "
                              f"[{seg.train.name}] ({seg.trip_minutes} min)")
                        if idx < len(route['wait_times']):
                            print(f"      Time to change connection: {route['wait_times'][idx]} min")
                    print()

    elif args.summary:
        print_summary(g, top=args.head)
    elif args.city:
        print_city(g, args.city, limit=args.head)
    elif args.train:
        print_train(g, args.train, limit=args.head)
    else:
        # Default preview of first N connections
        print(f"Parsed {len(g.connections)} connections, "
              f"{len(g.cities.items)} cities, {len(g.trains.items)} trains\n")
        for c in g.connections[:args.head]:
            print(f"{c.route_id}: {c.dep_city.name} {c.dep_time} → "
                  f"{c.arr_city.name} {c.arr_time} "
                  f"({c.trip_minutes} min) [{c.train.name}]")


# Code runs only when module is executed (not when imported)
# Can be invoked with this cli command python "-m EURailNetwork data/eu_rail_network.csv --summary" or variations
if __name__ == "__main__":
    main()

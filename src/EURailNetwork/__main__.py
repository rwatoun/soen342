import argparse
from .loader import read_raw_csv, build_network_from_df
from .inspectors import (
    print_summary,
    print_city,
    print_train,
    print_connection_search_results,
)
from .utils_time import parse_time
from colorama import Fore, Style


def main():
    import sys

    p = argparse.ArgumentParser()
    p.add_argument("csv_path", help="Path to the data file (e.g. data/eu_rail_network.csv)")
    args = p.parse_args()

    # Build network from CSV
    df = read_raw_csv(args.csv_path)
    g = build_network_from_df(df)

    print(Fore.GREEN + "\nWelcome to the EURail Network CLI!" + Style.RESET_ALL)

    # --- menu loop ---
    while True:
        print(Fore.CYAN + "\nPlease select an option:" + Style.RESET_ALL)
        print("1. View Network Summary")
        print("2. Search for a Connection (Direct or Indirect)")
        print("3. Find City Information")
        print("4. Find Train Information")
        print("5. Exit")

        choice = input(Fore.YELLOW + "\nEnter your choice (1–5): " + Style.RESET_ALL).strip()

        # --- Option 1: Summary ---
        if choice == "1":
            print(Fore.CYAN + "\n=== NETWORK SUMMARY ===" + Style.RESET_ALL)
            print_summary(g, top=1200)

        # --- Option 2: Connection search ---
        elif choice == "2":
            print(Fore.CYAN + "\n=== CONNECTION SEARCH ===" + Style.RESET_ALL)
            from_city = input("From city: ").strip()
            to_city = input("To city: ").strip()

            print(Fore.YELLOW + "\nSearching for direct connections..." + Style.RESET_ALL)
            connections = g.search_connections(depart_city=from_city, arrival_city=to_city)

            if connections:
                print_connection_search_results(connections, sort_by="dep_time", ascending=True)
            else:
                print(Fore.YELLOW + "\nNo direct connections found — searching for indirect routes..." + Style.RESET_ALL)
                routes = g.find_indirect_connections(from_city, to_city)

                if not routes or len(routes) == 0:
                    print(Fore.RED + "No indirect routes found." + Style.RESET_ALL)
                else:
                    routes.sort(key=lambda r: r["total_minutes"])
                    print(Fore.GREEN + f"\nFound {len(routes)} indirect route(s):" + Style.RESET_ALL)
                    for i, route in enumerate(routes, 1):
                        total_h, total_m = divmod(route["total_minutes"], 60)
                        print(Fore.CYAN + f"\nROUTE #{i} (Total Duration: {total_h}h{total_m:02d}m)" + Style.RESET_ALL)
                        for idx, seg in enumerate(route["segments"]):
                            print(f"  {seg.dep_city.name:>10} {seg.dep_time.strftime('%H:%M')} → "
                                  f"{seg.arr_city.name:<15} {seg.arr_time.strftime('%H:%M')} "
                                  f"[{seg.train.name}] ({seg.trip_minutes} min)")
                            if idx < len(route["wait_times"]):
                                print(f"    Time to change connection: {route['wait_times'][idx]} min")
                        print()

        # --- Option 3: City info ---
        elif choice == "3":
            city = input("Enter city name: ").strip()
            print(Fore.CYAN + f"\n=== CITY INFORMATION: {city} ===" + Style.RESET_ALL)
            print_city(g, city, limit=1200)

        # --- Option 4: Train info ---
        elif choice == "4":
            train = input("Enter train name: ").strip()
            print(Fore.CYAN + f"\n=== TRAIN INFORMATION: {train} ===" + Style.RESET_ALL)
            print_train(g, train, limit=1200)

        # --- Option 5: Exit ---
        elif choice == "5":
            print(Fore.MAGENTA + "\nGoodbye! Thanks for using EURail Network.\n" + Style.RESET_ALL)
            sys.exit(0)

        # --- Invalid choice ---
        else:
            print(Fore.RED + "Invalid choice. Please try again." + Style.RESET_ALL)


# Code runs only when module is executed (not when imported)
# Can be invoked with this cli command python "-m EURailNetwork data/eu_rail_network.csv --summary" or variations
if __name__ == "__main__":
    main()

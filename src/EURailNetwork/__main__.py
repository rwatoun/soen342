import argparse
from colorama import Fore, Style, init
from datetime import datetime, time as dt_time
from . import db_sqlite

from EURailNetwork.registries import BookingSystem
from .loader import read_raw_csv, build_network_from_df
from .inspectors import (
    print_summary,
    print_city,
    print_train,
    print_connection_search_results,
    print_indirect_connection_results
)
from .utils_time import parse_time


init(autoreset=True)

def ask_yes_no(prompt: str) -> bool:
    ans = input(Fore.YELLOW + prompt + " (y/n): " + Style.RESET_ALL).strip().lower()
    return ans in ("y", "yes", "")


def ask_optional_int(prompt: str):
    val = input(Fore.CYAN + prompt + " (leave blank for none): " + Style.RESET_ALL).strip()
    return int(val) if val else None


def ask_optional_time(prompt: str):
    val = input(Fore.CYAN + prompt + " (HH:MM or blank): " + Style.RESET_ALL).strip()
    return parse_time(val) if val else None

def collect_traveller_info() -> list[dict]:
    travellers = []

    while True:
        print(Fore.MAGENTA + "\nEnter Traveller Information:" + Style.RESET_ALL)
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()

        while True:
            try:
                age_input = input("Age: ").strip()
                age = int(age_input)
                if age < 0 or age > 150:
                    print(Fore.RED + "Please enter a valid age (0-150)." + Style.RESET_ALL)
                    continue
                break
            except ValueError:
                print(Fore.RED + "Invalid input. Please enter a number for age." + Style.RESET_ALL)
        
        traveller_id = input("ID (passport / state ID): ").strip()

        travellers.append({
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "id": traveller_id
        })

        if not ask_yes_no("Do you want to add another traveller?"): 
            break

    return travellers

def book_trip_flow(g, booking_system):
    print(Fore.MAGENTA + "\n=== Book A Trip ===" + Style.RESET_ALL)

    # 1 Search for a connection
    print(Fore.YELLOW + "Find your connection" + Style.RESET_ALL)
    depart_city = input("Departure city: ").strip().lower()
    arrival_city = input("Arrival city: ").strip().lower()

    direct_connections = g.search_connections(depart_city=depart_city, arrival_city=arrival_city)
    indirect_connections = g.find_indirect_connections(from_city=depart_city, to_city=arrival_city)

    # check if there are any connections
    if not indirect_connections and not direct_connections:
        print(Fore.RED + "No connections found between the specified cities. Booking process aborted." + Style.RESET_ALL)
        return None

    # display direct connections 
    if direct_connections:
        print_connection_search_results(direct_connections)
    else:
        print(Fore.RED + "No direct connections found." + Style.RESET_ALL)

    # display indirect connections 
    if indirect_connections:
        print_indirect_connection_results(indirect_connections)
    else: 
        print(Fore.RED + "No indirect connections found." + Style.RESET_ALL)

    # Combine all connections for selection
    all_connections = []
    all_connections.extend(direct_connections)
    for route in indirect_connections:
        all_connections.append(route["segments"])
    
        # 2 Client selects a connection
    try:
        choice = int(input(Fore.CYAN + "Select connection by number: " + Style.RESET_ALL).strip())
        selected_connection = all_connections[choice - 1]
    except (ValueError, IndexError):
        print(Fore.RED + "Invalid selection. Booking process aborted." + Style.RESET_ALL)
        return
        
    # 3 Collect traveller info
    travellers_data = collect_traveller_info()

    # 4.1  Book trip
    try:
        trip = booking_system.book_trip(selected_connection, travellers_data)

        # 4.2 Display booking confirmation
        print(Fore.GREEN + "\n=== Booking Confirmation ===" + Style.RESET_ALL)

        # 4.3 Display Trip info
        print(f"Trip ID: {trip.id}")
        print(f"Route: {trip.connections[0].dep_city.name} → {trip.connections[0].arr_city.name}")
        print(f"Departure time: {trip.connections[0].dep_time.strftime('%H:%M')}")
        print(f"Arrival time: {trip.connections[0].arr_time.strftime('%H:%M')}")
        print(f"Number of reservations/travellers: {len(trip.reservations)}")

        # 4.4 Print tickets
        print(Fore.CYAN + "\n=== Your Tickets ====" + Style.RESET_ALL)
        for reservation in trip.reservations:
            print(f"{reservation.traveller.first_name} {reservation.traveller.last_name} {reservation.traveller.age} - Ticket #{reservation.ticket.id}")

        print("\nThank you for booking with EURail Network Interactive CLI.\n")
        return trip
    except Exception as e:
        print(Fore.RED + f"Booking failed due to: {e}" + Style.RESET_ALL)
        return None
        
# To view past trips
def view_trips_flow(booking_system):

    print(Fore.MAGENTA + "\n=== View My Trips ===" + Style.RESET_ALL)
    last_name = input(Fore.CYAN + "Enter your last name: " + Style.RESET_ALL).strip()
    traveller_id = input(Fore.CYAN + "Enter your ID (passport/state ID): " + Style.RESET_ALL).strip()
    
    traveller = booking_system.travellers.by_key.get(traveller_id)
    
    if traveller is None:
        print(Fore.RED + f"No traveller found with ID '{traveller_id}'." + Style.RESET_ALL)
        return
    
    if traveller.last_name.lower() != last_name.lower():
        print(Fore.RED + f"Last name does not match for ID '{traveller_id}'." + Style.RESET_ALL)
        return
    
    trips = traveller.list_trips()
    
    if not trips:
        print(Fore.YELLOW + f"\nNo trips found for {traveller.first_name} {traveller.last_name}." + Style.RESET_ALL)
        return
    
    # Separate trips into upcoming/future and past
    # Note: Since we don't have actual dates, all trips are shown as upcoming/future
    upcoming_trips = trips
    past_trips = []
    
    print(Fore.GREEN + f"\n=== Trip History for {traveller.first_name} {traveller.last_name} ===" + Style.RESET_ALL)
    print(Fore.CYAN + f"Total trips: {len(trips)}" + Style.RESET_ALL)
    print(Fore.CYAN + f"Upcoming/Future trips: {len(upcoming_trips)}" + Style.RESET_ALL)
    print(Fore.CYAN + f"Past trips: {len(past_trips)}" + Style.RESET_ALL)
    
    # Display list of trips with summary
    while True:
        if upcoming_trips:
            print(Fore.GREEN + f"\n=== Upcoming/Future Trips ===" + Style.RESET_ALL)
            display_trips_list(upcoming_trips, traveller)
        
        if past_trips:
            print(Fore.LIGHTBLACK_EX + f"\n=== Past Trips ===" + Style.RESET_ALL)
            display_trips_list(past_trips, traveller)
        
        print(Fore.YELLOW + "\nOptions:" + Style.RESET_ALL)
        print("  Enter trip number to view details")
        print("  Or press Enter to go back to main menu")
        
        choice = input(Fore.CYAN + "Your choice: " + Style.RESET_ALL).strip()
        
        if not choice:
            break
        
        try:
            trip_num = int(choice)
            if 1 <= trip_num <= len(trips):
                display_trip_details(trips[trip_num - 1], traveller)
            else:
                print(Fore.RED + f"Invalid trip number. Please enter 1-{len(trips)}" + Style.RESET_ALL)
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a number or press Enter." + Style.RESET_ALL)

def display_trips_list(trips, current_traveller):
    for i, trip in enumerate(trips, 1):
        if trip.connections:
            conn = trip.connections[0]
            traveller_count = len(trip.reservations)
            status = "Upcoming"  
            
            print(f"{i}. Trip {trip.id} | {conn.dep_city.name} → {conn.arr_city.name} | "
                  f"Dep: {conn.dep_time.strftime('%H:%M')} | {traveller_count} traveller(s) | "
                  f"Status: {status}")

def display_trip_details(trip, current_traveller):
    print(Fore.YELLOW + f"\n{'=' * 70}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"TRIP DETAILS" + Style.RESET_ALL)
    print(Fore.YELLOW + f"{'=' * 70}" + Style.RESET_ALL)
    
    print(Fore.GREEN + f"\nTrip ID: {trip.id}" + Style.RESET_ALL)
    print(f"Status: Upcoming/Future")  
    
    # Display connection information
    if trip.connections:
        conn = trip.connections[0]
        print(Fore.CYAN + f"\n--- Connection Information ---" + Style.RESET_ALL)
        print(f"Route: {conn.dep_city.name} → {conn.arr_city.name}")
        print(f"Train: {conn.train.name}")
        print(f"Departure: {conn.dep_time.strftime('%H:%M')}")
        print(f"Arrival: {conn.arr_time.strftime('%H:%M')}")
        print(f"Duration: {conn.trip_minutes} minutes ({conn.trip_minutes // 60}h {conn.trip_minutes % 60}m)")
        print(f"First Class Price: €{conn.first_class_eur}")
        print(f"Second Class Price: €{conn.second_class_eur}")
    
    # Display travellers and ticket information
    print(Fore.CYAN + f"\n--- Travellers & Tickets ---" + Style.RESET_ALL)
    for reservation in trip.reservations:
        marker = "(You)" if reservation.traveller.id == current_traveller.id else ""
        print(f"  • {reservation.traveller.first_name} {reservation.traveller.last_name}, "
              f"Age {reservation.traveller.age}")
        print(f"    Ticket #: {reservation.ticket.id}{marker}")
    
    print(Fore.YELLOW + f"\n{'=' * 70}" + Style.RESET_ALL)
    
    # Wait for user to go back
    input(Fore.CYAN + "\nPress Enter to go back to trip list..." + Style.RESET_ALL)


# --- Main CLI ---
def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    p.add_argument("--head", type=int, default=1200,
                   help="Number of connections to preview (default=1200)")
    args = p.parse_args()

    # Load dataset
    df = read_raw_csv(args.csv_path)
    g = build_network_from_df(df)
    booking_system = BookingSystem(railNetwork=g)

    # sqlite loading ***********************************************!!!!
    conn = db_sqlite.connect("eurail.db") 
    db_sqlite.migrate(conn)

    # save static network 
    db_sqlite.save_network(conn, g)

    # load previously saved trips/reservations from db into memory
    db_sqlite.load_trips(conn, booking_system, g)



    # booking_system.load_trips() no loads from json we only want db

    print(Fore.MAGENTA + "\nEURail Network Interactive CLI" + Style.RESET_ALL)
    print(Fore.LIGHTBLACK_EX + "----------------------------------------------\n" + Style.RESET_ALL)

    while True:
        print(Fore.CYAN + "=== MAIN MENU ===" + Style.RESET_ALL)
        print(Fore.GREEN + "1." + Style.RESET_ALL, "View Network Summary")
        print(Fore.GREEN + "2." + Style.RESET_ALL, "Search for a Connection")
        print(Fore.GREEN + "3." + Style.RESET_ALL, "View City Info")
        print(Fore.GREEN + "4." + Style.RESET_ALL, "View Train Info")
        print(Fore.GREEN + "5." + Style.RESET_ALL, "Book a Trip")
        print(Fore.GREEN + "6." + Style.RESET_ALL, "View My Trips")
        print(Fore.RED + "7." + Style.RESET_ALL, "Exit")

        choice = input(Fore.YELLOW + "\nEnter your choice (1-7): " + Style.RESET_ALL).strip()

        # --- Option 1: Summary ---
        if choice == "1":
            print_summary(g, top=args.head)

        # --- Option 2: Connection search ---
        elif choice == "2":
            print(Fore.MAGENTA + "\nConnection Search\n" + Style.RESET_ALL)

            depart_city = input(Fore.CYAN + "Departure city: " + Style.RESET_ALL).strip().lower()
            arrival_city = input(Fore.CYAN + "Arrival city: " + Style.RESET_ALL).strip().lower()

            # Default filter values
            train_type = None
            min_first_class_price = max_first_class_price = None
            min_second_class_price = max_second_class_price = None
            min_departure_time = max_departure_time = None
            min_arrival_time = max_arrival_time = None
            min_duration = max_duration = None
            weekday = None

            print(Fore.LIGHTGREEN_EX + "\nFILTER SELECTION" + Style.RESET_ALL)
            print(Fore.LIGHTBLACK_EX + "Choose which filters to apply before searching.\n" + Style.RESET_ALL)

            use_train_filter = ask_yes_no("Do you want to filter by train type?")
            use_price_filter = ask_yes_no("Do you want to filter by price?")
            use_time_filter = ask_yes_no("Do you want to filter by time?")
            use_duration_filter = ask_yes_no("Do you want to filter by duration?")
            use_weekday_filter = ask_yes_no("Do you want to filter by weekday?")
            use_sorting = ask_yes_no("Do you want to sort the results?")

            if use_train_filter:
                train_type = input(Fore.CYAN + "  Enter train type (e.g., InterCity, TGV, etc.): " + Style.RESET_ALL).strip()

            if use_price_filter:
                print(Fore.LIGHTGREEN_EX + "\nPRICE FILTERS" + Style.RESET_ALL)
                min_first_class_price = ask_optional_int("  Minimum first-class price (€)")
                max_first_class_price = ask_optional_int("  Maximum first-class price (€)")
                min_second_class_price = ask_optional_int("  Minimum second-class price (€)")
                max_second_class_price = ask_optional_int("  Maximum second-class price (€)")

            if use_time_filter:
                print(Fore.LIGHTGREEN_EX + "\nTIME FILTERS" + Style.RESET_ALL)
                min_departure_time = ask_optional_time("  Earliest departure time")
                max_departure_time = ask_optional_time("  Latest departure time")
                min_arrival_time = ask_optional_time("  Earliest arrival time")
                max_arrival_time = ask_optional_time("  Latest arrival time")

            if use_duration_filter:
                print(Fore.LIGHTGREEN_EX + "\nDURATION FILTERS" + Style.RESET_ALL)
                min_duration = ask_optional_int("  Minimum duration (minutes)")
                max_duration = ask_optional_int("  Maximum duration (minutes)")

            if use_weekday_filter:
                weekday = ask_optional_int("  Enter weekday (0=Mon ... 6=Sun)")

            sort_by = "dep_time"
            ascending = True
            if use_sorting:
                print(Fore.LIGHTGREEN_EX + "\nSORTING OPTIONS" + Style.RESET_ALL)
                sort_by = input(
                    Fore.CYAN +
                    "  Sort by [dep_time, arr_time, trip_minutes, first_class_eur, second_class_eur]: "
                    + Style.RESET_ALL
                ).strip() or "dep_time"
                ascending = ask_yes_no("  Sort ascending?")

            print(Fore.YELLOW + "\nSearching for connections...\n" + Style.RESET_ALL)

            connections = g.search_connections(
                depart_city=depart_city,
                arrival_city=arrival_city,
                train_type=train_type,
                min_first_class_price=min_first_class_price,
                max_first_class_price=max_first_class_price,
                min_second_class_price=min_second_class_price,
                max_second_class_price=max_second_class_price,
                min_departure_time=min_departure_time,
                max_departure_time=max_departure_time,
                min_arrival_time=min_arrival_time,
                max_arrival_time=max_arrival_time,
                min_duration=min_duration,
                max_duration=max_duration,
                weekday=weekday,
                sort_by=sort_by,
                ascending=ascending,
            )

            # --- Display Results ---
            if connections:
                print_connection_search_results(connections, sort_by, ascending)
            else:
                print(Fore.RED + "\nNo direct connections found — searching for indirect routes...\n" + Style.RESET_ALL)
                routes = g.find_indirect_connections(depart_city, arrival_city)

                # --- Apply all filters to indirect routes ---
                if routes:
                    filtered_routes = []
                    for route in routes:
                        valid = True
                        total_duration = route["total_minutes"]

                        for seg in route["segments"]:
                            # Train type
                            if train_type and seg.train.name.lower() != train_type.lower():
                                valid = False
                                break
                            # Prices
                            if min_first_class_price is not None and seg.first_class_eur < min_first_class_price:
                                valid = False
                                break
                            if max_first_class_price is not None and seg.first_class_eur > max_first_class_price:
                                valid = False
                                break
                            if min_second_class_price is not None and seg.second_class_eur < min_second_class_price:
                                valid = False
                                break
                            if max_second_class_price is not None and seg.second_class_eur > max_second_class_price:
                                valid = False
                                break
                            # Time filters
                            if min_departure_time and seg.dep_time < min_departure_time:
                                valid = False
                                break
                            if max_departure_time and seg.dep_time > max_departure_time:
                                valid = False
                                break
                            if min_arrival_time and seg.arr_time < min_arrival_time:
                                valid = False
                                break
                            if max_arrival_time and seg.arr_time > max_arrival_time:
                                valid = False
                                break
                            # Weekday filter
                            if weekday is not None and weekday not in seg.days:
                                valid = False
                                break
                        # Duration filter on total route
                        if valid:
                            if min_duration is not None and total_duration < min_duration:
                                valid = False
                            if max_duration is not None and total_duration > max_duration:
                                valid = False
                        if valid:
                            filtered_routes.append(route)
                    routes = filtered_routes

                # --- Display filtered results ---
                if not routes:
                    print(Fore.RED + "No indirect routes found matching your filters." + Style.RESET_ALL)
                else:
                    print(Fore.GREEN + f"Found {len(routes)} indirect route(s):\n" + Style.RESET_ALL)
                    for i, route in enumerate(routes, 1):
                        total_h, total_m = divmod(route["total_minutes"], 60)
                        print(
                            Fore.YELLOW
                            + f"ROUTE #{i}: "
                            + Style.RESET_ALL
                            + f"Total Duration: {total_h}h{total_m:02d}m"
                        )
                        for idx, seg in enumerate(route["segments"]):
                            dur_str = f"{seg.trip_minutes // 60}h{seg.trip_minutes % 60:02d}m"
                            print(
                                f"    {seg.dep_city.name:>10} {seg.dep_time.strftime('%H:%M')} → "
                                f"{seg.arr_city.name:<15} {seg.arr_time.strftime('%H:%M')} "
                                f"[{seg.train.name}] ({dur_str})"
                            )
                            print(f"         1st: {seg.first_class_eur}€ | 2nd: {seg.second_class_eur}€")
                            if idx < len(route['wait_times']):
                                print(Fore.LIGHTBLACK_EX + f"         Wait: {route['wait_times'][idx]} min" + Style.RESET_ALL)
                        print(Fore.LIGHTBLACK_EX + "-" * 70 + Style.RESET_ALL)

        # --- Option 3: City info ---
        elif choice == "3":
            city = input(Fore.CYAN + "Enter city name: " + Style.RESET_ALL).strip().lower()
            print_city(g, city, limit=args.head)

        # --- Option 4: Train info ---
        elif choice == "4":
            train = input(Fore.CYAN + "Enter train name: " + Style.RESET_ALL).strip().lower()
            print_train(g, train, limit=args.head)

        # --- Option 5: Book a Trip ---
        elif choice == "5":
            trip = book_trip_flow(g, booking_system)
            if trip:
                # booking_system.save_trips() now we want to save to db directly
                try:
                    db_sqlite.save_trip(conn, trip)
                except Exception as e:
                    print(Fore.RED + f"Can't persist trip to DB: {e}" + Style.RESET_ALL)

        # --- Option 6: View My Trips ---
        elif choice == "6":
            view_trips_flow(booking_system)
        
        # --- Option 7: Exit ---
        elif choice == "7":
            # Save all trip data before exiting
            booking_system.save_trips() 
            print(Fore.LIGHTRED_EX + "\nExiting the program. Goodbye.\n" + Style.RESET_ALL)
            break

        else:
            print(Fore.RED + "Invalid choice. Please enter a number between 1 and 7.\n" + Style.RESET_ALL)


# Code runs only when module is executed (not when imported)
# Can be invoked with this cli command python "-m EURailNetwork data/eu_rail_network.csv --summary" or variations
if __name__ == "__main__":
    main()

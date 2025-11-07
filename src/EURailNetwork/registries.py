from __future__ import annotations
from dataclasses import dataclass, field
import sqlite3
from typing import Dict

from .models import City, Train, Connection, Traveller, Trip, Reservation, Ticket

from datetime import time
import unicodedata
from typing import Dict, List, Optional
import random
import string


# this function helps normalize the data by trimming and collapsing spaces
def norm_name(name: str) -> str:
    """Normalize a name for reliable matching (case-insensitive, no accents or extra spaces)."""
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return " ".join(name.strip().split()).casefold()

# class cities holds a list and a dictionnary of cities from which it can fetch specific ones or create ones based on names
@dataclass
class Cities:
    by_key: Dict[str, City] = field(default_factory=dict)
    items: list[City] = field(default_factory=list)

    def get_or_create(self, name: str) -> City:
        key = norm_name(name)
        found = self.by_key.get(key)
        if found:
            return found
        obj = City(name=name.strip())
        self.by_key[key] = obj
        self.items.append(obj)
        return obj

@dataclass
class Trains:
    by_key: Dict[str, Train] = field(default_factory=dict)
    items: list[Train] = field(default_factory=list)

    def get_or_create(self, name: str) -> Train:
        key = norm_name(name)
        found = self.by_key.get(key)
        if found:
            return found
        obj = Train(name=name.strip())
        self.by_key[key] = obj
        self.items.append(obj)
        return obj

# this is the class that models the system. it holds all cities, trains, and connections. this method adds a new 
# connection to the system as it reads the csv file and updates the departure and arrival cities and train type.
@dataclass
class RailNetwork:
    cities: Cities = field(default_factory=Cities)
    trains: Trains = field(default_factory=Trains)
    connections: list[Connection] = field(default_factory=list)

    def add_connection(self, conn: Connection) -> None:
        self.connections.append(conn)
        # from the network you can find all connections. 
        # from a city you can see all the trains that arrive and depart. 
        # from a train type you can see all the connections it runs on.
        conn.dep_city.departures.append(conn)
        conn.arr_city.arrivals.append(conn)
        conn.train.connections.append(conn)
    
    # this method is called by the test for search and sort to validate that everyhting works well
    # for the search of items
    def find_direct(self, depart_city: str, arrival_city: str, weekday: int | None = None):
        def _norm(s: str): return " ".join(s.strip().split()).casefold()
        dep_k, arr_k = _norm(depart_city), _norm(arrival_city)
        return [
            c for c in self.connections
            if _norm(c.dep_city.name) == dep_k
            and _norm(c.arr_city.name) == arr_k
            and (weekday is None or weekday in c.days)
        ]

    # this method is called by the test for search and sort to validate that everyhting works well 
    # for the sorting of the connections
    @staticmethod
    def sort_connections(conns, by: str, ascending: bool = True, price_class: str | None = None):
        if by == "trip_minutes":
            key = lambda c: (c.trip_minutes, c.dep_time, c.route_id)
        elif by == "price":
            key = (lambda c: (c.first_class_eur, c.dep_time, c.route_id)) if price_class == "first" \
                else (lambda c: (c.second_class_eur, c.dep_time, c.route_id))
        elif by == "dep_time":
            key = lambda c: (c.dep_time, c.route_id)
        else:
            raise ValueError(f"Unsupported sort key: {by}")
        return sorted(conns, key=key, reverse=not ascending)
    
    def search_connections(
        self,
        depart_city: str = None,
        arrival_city: str = None,
        train_type: str = None,
        min_first_class_price: int = None,
        max_first_class_price: int = None,
        min_second_class_price: int = None,
        max_second_class_price: int = None,
        min_departure_time: time = None,
        max_departure_time: time = None,
        min_arrival_time: time = None,
        max_arrival_time: time = None,
        min_duration: int = None,
        max_duration: int = None,
        weekday: int = None,
        sort_by: str = "dep_time",
        ascending: bool = True
    ) -> list[Connection]:

        results = self.connections.copy()

        # Filter by departure city
        if depart_city:
            dep_pattern = norm_name(depart_city)
            results = [c for c in results if dep_pattern in norm_name(c.dep_city.name)]
        if arrival_city:
            arr_pattern = norm_name(arrival_city)
            results = [c for c in results if arr_pattern in norm_name(c.arr_city.name)]

        # Filter by train type
        # Exact same logic as depart_city case
        if train_type:
            t_pattern = norm_name(train_type)
            results = [c for c in results if t_pattern in norm_name(c.train.name)]

        # Filter by first class price
        # Client can provide 2 first class prices: min and max, and the system will fetch connections between these 2 prices
        if min_first_class_price is not None:
            results = [c for c in results if min_first_class_price <= c.first_class_eur]
        if max_first_class_price is not None:
            results = [c for c in results if c.first_class_eur <= max_first_class_price]
        if min_second_class_price is not None:
            results = [c for c in results if min_second_class_price <= c.second_class_eur]
        if max_second_class_price is not None:
            results = [c for c in results if c.second_class_eur <= max_second_class_price]

        # Time filters
        if min_departure_time is not None:
            results = [c for c in results if min_departure_time <= c.dep_time]
        if max_departure_time is not None:
            results = [c for c in results if c.dep_time <= max_departure_time]
        if min_arrival_time is not None:
            results = [c for c in results if min_arrival_time <= c.arr_time]
        if max_arrival_time is not None:
            results = [c for c in results if c.arr_time <= max_arrival_time]

        # Duration filters
        if min_duration is not None:
            results = [c for c in results if min_duration <= c.trip_minutes]
        if max_duration is not None:
            results = [c for c in results if c.trip_minutes <= max_duration]

        # Weekday filter
        if weekday is not None:
            results = [c for c in results if weekday in c.days]

        # Sorting
        if sort_by == "dep_city":
            key = lambda c: (c.dep_city.name.lower(), c.dep_time, c.route_id)
        elif sort_by == "arr_city":
            key = lambda c: (c.arr_city.name.lower(), c.dep_time, c.route_id)
        elif sort_by == "train_name":
            key = lambda c: (c.train.name.lower(), c.dep_time, c.route_id)
        elif sort_by == "first_class_eur":
            key = lambda c: (c.first_class_eur, c.dep_time, c.route_id)
        elif sort_by == "second_class_eur":
            key = lambda c: (c.second_class_eur, c.dep_time, c.route_id)
        elif sort_by == "dep_time":
            key = lambda c: (c.dep_time, c.arr_time, c.route_id)
        elif sort_by == "arr_time":
            key = lambda c: (c.arr_time, c.dep_time, c.route_id)
        elif sort_by == "trip_minutes":
            key = lambda c: (c.trip_minutes, c.dep_time, c.route_id)
        else:
            key = lambda c: (c.dep_time, c.route_id)

        return sorted(results, key=key, reverse=not ascending)

    # --- Indirect Connections (1-stop and 2-stop) ---
    def find_indirect_connections(self, from_city: str, to_city: str, max_stops: int = 2):
        """
        Find all possible 1-stop and 2-stop routes between two cities.
        Includes waiting times and supports next-day departures.
        """
        from .utils_time import calculate_wait_time
        results = []

        from_key = norm_name(from_city)
        to_key = norm_name(to_city)
        
        adj = {}
        for c in self.connections:
            dep = norm_name(c.dep_city.name)
            adj.setdefault(dep, []).append(c)

        # --- 1-STOP (A → B → C) ---
        if from_key in adj:
            for c1 in adj[from_key]:
                mid_key = norm_name(c1.arr_city.name)
                if mid_key not in adj:
                    continue
                for c2 in adj[mid_key]:
                    if norm_name(c2.arr_city.name) == to_key:
                        wait = calculate_wait_time(c1.arr_time, c2.dep_time)
                        total = c1.trip_minutes + c2.trip_minutes + wait
                        results.append({
                            "segments": [c1, c2],
                            "wait_times": [wait],
                            "total_minutes": total,
                        })

        # --- 2-STOP (A → B → C → D) ---
        if max_stops >= 2 and from_key in adj:
            for c1 in adj[from_key]:
                mid1_key = norm_name(c1.arr_city.name)
                if mid1_key not in adj:
                    continue
                for c2 in adj[mid1_key]:
                    mid2_key = norm_name(c2.arr_city.name)
                    if mid2_key not in adj:
                        continue
                    for c3 in adj[mid2_key]:
                        if norm_name(c3.arr_city.name) == to_key:
                            wait1 = calculate_wait_time(c1.arr_time, c2.dep_time)
                            wait2 = calculate_wait_time(c2.arr_time, c3.dep_time)
                            total = (
                                c1.trip_minutes + c2.trip_minutes + c3.trip_minutes
                                + wait1 + wait2
                            )
                            results.append({
                                "segments": [c1, c2, c3],
                                "wait_times": [wait1, wait2],
                                "total_minutes": total,
                            })

        # --- Deduplicate routes ---
        unique = []
        seen = set()
        for r in results:
            key = tuple(seg.route_id for seg in r["segments"])
            if key not in seen:
                unique.append(r)
                seen.add(key)

        #print(f"DEBUG: Found {len(unique)} indirect route(s) from {from_city} → {to_city}")
        return unique

# helper method for normalizing the name input
def norm_name(name: str) -> str:
    return name.strip().lower()

@dataclass
class Travellers:
    by_key:Dict[str, Traveller] = field(default_factory=dict)
    
    items: list[Traveller] = field(default_factory=list)

    def get_or_create(self, first_name: str, last_name: str, age: int, id: str) -> Traveller:
        found = self.by_key.get(id)
        if found:
            return found # If traveller exists, return it. stops here
        # If traveller doesn't exist, create an instance
        traveller = Traveller(first_name=first_name, last_name=last_name, age=age, id=id)
        self.by_key[id] = traveller
        self.items.append(traveller)
        return traveller # Return newly created traveller
    
    def find_by_id(self, id_: str) -> Optional[Traveller]:
        for traveller in self.items:
            if traveller.id == id_:
                return traveller
       # return None # If can't find traveller from id (doesn't exist), return None

    # Same as find_by_id but for last name lookup
    def find_by_last_name(self, last_name:str) -> list[Traveller]:
        for traveller in self.items:
            if traveller.last_name == last_name:
                return traveller
        # return None
@dataclass
class Trips:
    by_id: dict[str, Trip] = field(default_factory=dict)
    items: list[Trip] = field(default_factory=list)

    def create_full_trip(
        self,
        connection: Connection,
        travellers: List[Traveller],
        reservations_registry: Reservations
    ) -> Trip:

        # Create the trip (auto id)
        trip = Trip(connection=connection)
        trip.connections.append(connection)

        # Register trip
        for traveller in travellers:
            ticket = Ticket(reservation=None) # Just a placeholder
            reservation = Reservation(traveller=traveller, ticket=ticket, trip=trip)
            ticket.reservation = reservation

            trip.add_reservation(reservation)
            traveller.add_reservation(reservation)
            reservations_registry.add(reservation)

        self.by_id[trip.id] = trip
        self.items.append(trip)

        # Return the fully constructed trip object
        return trip
    
    def find_trips_by_traveller_id(self, traveller_id: str) -> list[Trip]:
        trips = [] # If there aren't any trips, return an empty list (but shouldn't happen because for a traveller to register, needs to book a trip)
        
        for trip in self.items:
            for reservation in trip.reservations:
                if reservation.traveller.id == traveller_id:
                    trips.append(trip)
                    break

        return trips
    
    def find_trips_by_traveller_last_name(self, last_name:str) -> list[Trip]:
        trips = []

        for trip in self.items:
            for reservation in trip.reservations:
                if reservation.traveller.last_name == last_name:
                    trips.append(trip)
                    break
        return trips

@dataclass
class Reservations:
    items: list[Reservation] = field(default_factory=list)

    def add(self, reservation: Reservation):
        self.items.append(reservation)

    def find_by_traveller(self, traveller: Traveller) -> list[Reservation]:
        return [r for r in self.items if r.traveller is traveller]

    def find_by_trip(self, trip: Trip) -> list[Reservation]:
        return [r for r in self.items if r.trip is trip]
    
@dataclass
class BookingSystem:
# Manages data (bookings, travellers, and trips)
# Controls booking process
# Provides view trips given traveller info

    railNetwork: RailNetwork
    travellers: Travellers = field(default_factory=Travellers)
    trips: Trips = field(default_factory=Trips)
    db_connection: sqlite3.Connection = None

    # This is the method that will generate an alphanumeric ID for every trip
    # Moved from models.py
    @staticmethod
    def generate_trip_id() -> str:
        letters = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TRP-{letters}"

    def book_trip(self, connections: Connection | list[Connection], traveller_data: list[dict]) -> Trip: # Also creates trip object
        # convert single connections into list
        if isinstance(connections, Connection):
            connections = [connections]

        # validate connection - Connection selected need to exist to be booked and to create a trip
        for c in connections:
            if c not in self.railNetwork.connections:
                raise ValueError("Connection not found in rail network") # If there are no connections, stop here and raise error
        
        # validate layover duration with a temporary trip id (trip layover needs to be validated before its id is generated)
        t = Trip(id="temp")
        t.connections.extend(connections)
        if not t.validate_layover() and len(connections) > 1: # only for multi connection trips
            raise ValueError("Trip doesn't satisfy our layover rules.")

        # generate unique trip id
        trip_id = self.generate_trip_id()

        # create trip
        trip = Trip(id=trip_id)
        trip.connections.extend(connections)

        travellers = []
        for data in traveller_data:
            # Creates/Gets traveller for every traveller data provided
            traveller = self.travellers.get_or_create(
                first_name=data["first_name"],
                last_name=data["last_name"],
                age=data["age"],
                id=data["id"]
            )
            travellers.append(traveller) # Add each traveller to list

        for traveller in travellers:
            ticket = Ticket(reservation=None)
            reservation = Reservation(
                traveller=traveller,
                ticket=ticket,
                trip=trip
            )
            ticket.reservation = reservation
            trip.add_reservation(reservation)
            traveller.add_reservation(reservation)

        self.trips.items.append(trip)
        self.trips.by_id[trip.id] = trip
        
        self.save_trip_to_db(trip=trip)
        
        return trip
    
    def view_trips_given_traveller(self, traveller_last_name: str, traveller_id: str = None) -> list[Trip]:
        if traveller_id:
            return self.trips.find_trips_by_traveller_id(traveller_id)
        else:
            return self.trips.find_trips_by_traveller_last_name(traveller_last_name)
    
    def save_trips(self, filepath: str = "trip_data.json") -> None:
        #Save all trips and traveller data to JSON file.
        import json
        
        data = {
            "travellers": [],
            "trips": []
        }
        
        # Save travellers
        for traveller in self.travellers.items:
            data["travellers"].append({
                "first_name": traveller.first_name,
                "last_name": traveller.last_name,
                "age": traveller.age,
                "id": traveller.id
            })
        
        # Save trips
        for trip in self.trips.items:
            trip_data = {
                "id": trip.id,
                "connections": [],
                "reservations": []
            }
            
            # Save connections
            for conn in trip.connections:
                trip_data["connections"].append({
                    "route_id": conn.route_id,
                    "dep_city": conn.dep_city.name,
                    "arr_city": conn.arr_city.name,
                    "dep_time": conn.dep_time.strftime("%H:%M"),
                    "arr_time": conn.arr_time.strftime("%H:%M"),
                    "train": conn.train.name,
                    "first_class_eur": conn.first_class_eur,
                    "second_class_eur": conn.second_class_eur,
                    "trip_minutes": conn.trip_minutes
                })
            
            # Save reservations
            for reservation in trip.reservations:
                trip_data["reservations"].append({
                    "traveller_id": reservation.traveller.id,
                    "ticket_id": reservation.ticket.id
                })
            
            data["trips"].append(trip_data)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    # saving created trip to db using function in dq_sqlite.py
    def save_trip_to_db(self, trip: Trip, db_connection: sqlite3.Connection = None) -> None:
        if db_connection is None:
            print(f"Warning: No database connection found.")
            return
        
        try:
            from EURailNetwork.db_sqlite import save_trip
            save_trip(db_connection, trip)
            print(f"Trip {trip.id} successfully saved to database.")
        except Exception as e:
                print(f"Error: Could not save trip to database - {e}")
                # debug
                import traceback
                traceback.print_exc()

    def load_trips(self, filepath: str = "trip_data.json") -> None:
        # Load trips and traveller data from JSON file.
        import json
        import os
        
        if not os.path.exists(filepath):
            return 
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Load travellers
            traveller_map = {}
            for t_data in data.get("travellers", []):
                traveller = self.travellers.get_or_create(
                    first_name=t_data["first_name"],
                    last_name=t_data["last_name"],
                    age=t_data["age"],
                    id=t_data["id"]
                )
                traveller_map[t_data["id"]] = traveller
            
            # Load trips
            for trip_data in data.get("trips", []):
                route_id = trip_data["connections"][0]["route_id"]
                connection = None
                for conn in self.railNetwork.connections:
                    if conn.route_id == route_id:
                        connection = conn
                        break
                
                if connection is None:
                    continue 
                
                # Recreate trip
                trip = Trip(id=trip_data["id"])
                trip.connections.append(connection)
                
                # Recreate reservations
                for res_data in trip_data["reservations"]:
                    traveller = traveller_map.get(res_data["traveller_id"])
                    if traveller is None:
                        continue
                    
                    ticket = Ticket(reservation=None)
                    ticket.id = res_data["ticket_id"]
                    
                    reservation = Reservation(
                        traveller=traveller,
                        ticket=ticket,
                        trip=trip
                    )
                    ticket.reservation = reservation
                    
                    trip.add_reservation(reservation)
                    traveller.add_reservation(reservation)
                
                # Register trip
                self.trips.items.append(trip)
                self.trips.by_id[trip.id] = trip
                
        except Exception as e:
            print(f"Warning: Could not load saved trip data: {e}")
    





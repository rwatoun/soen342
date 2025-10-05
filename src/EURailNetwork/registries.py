from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable
from .models import City, Train, Connection

# this function helps normalize the data by trimming and collapsing spaces
def norm_name(name: str) -> str:
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
    
    def search_cities(self,
                      name_pattern: str=None,
                      min_departures: int = None,
                      min_arrivals: int = None,
                      sort_by: str = "name"
                      ) -> list[City]:
        
        results = self.cities.items.copy(); # Creating shallow copy of list of all cities

        # Making sure 
        if name_pattern:
            pattern = name_pattern.lower(); # Convert search term to lowercase for easier matching
            results = [city for city in results if pattern in city.name.lower()] # Looking for cities that contain search term as a substring (comparing to all lowercase cities)

        # Filtering by minimum departures
        if min_departures is not None:
            results = [city for city in results if len(city.departures) >= min_departures]

        # Filtering by minimum arrivals
        if min_arrivals is not None:
            results = [city for city in results if len(city.arrivals) >= min_arrivals]
        
        # Sorting
        if sort_by == "name":
            results.sort(key=lambda city: city.name)
        elif sort_by == "departures":
            results.sort(key=lambda city: city.departures, reverse=True) # Want to sort in descending order so True (same for sort_by arrivals)
        elif sort_by == "arrivals":
            results.sort(key=lambda city: city.departures, reverse=True)
        
        return results
    
    def search_trains(self, name_pattern: str=None, 
                      min_connections: int=None, 
                      sort_by: str="name") -> list[Train]:
        
        results = self.trains.items.copy(); # Shallow copy of all trains
        
        if name_pattern:
            pattern = name_pattern.lower(); # Convert search term to lowercase for easier matching
            results = [train for train in results if pattern in train.name.lower()]
        
        # If specify this argument, will return trains that have at least x number of connections
        if min_connections is not None:
            results = [train for train in results if len(train.connections) >= min_connections]

        # Sorting
        if sort_by == "name":
            results.sort(key=lambda train:train.name)
        if sort_by == "connections":
            results.sort(key=lambda train:len(train.connections), reverse=True)

        return results
    
    def search_ticket_price(self, max_price: int=None, min_price: int=None, price_class: str="second", sort_by: str="price"):
        results = self.connections.copy();

        # Filtering by price class (first or second-default)
        if price_class == "first":
            prices = [city.first_class_eur for city in results]
        else:
            prices = [city.second_class_eur for city in results]

        # Price filters
        if min_price is not None:
            if price_class == "first": # Still have to check price class
                results = [city for city in results if city.first_class_eur >= min_price]
            else:
                results = [city for city in results if city.second_class_eur >= min_price]

        if max_price is not None:
            if price_class == "first":
                results = [city for city in results if city.first_class_eur <= max_price]
            else:
                results = [city for city in results if city.second_class_eur <= max_price]
        
        # Sorting
        if sort_by == "price":
            if price_class == "first":
                results.sort(key=lambda city: city.first_class_eur)
            else:
                results.sort(key=lambda city: city.second_class_eur)
        elif sort_by == "dep_time":
            results.sort(key=lambda city: city.dep_time)

        return results
    
    

        

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time
from typing import FrozenSet
import random
import string

# because we later map the days of the week to integers for easier tracking 
Weekday = int  

# default_factory=list means that a new list is create for every new City instance
@dataclass
class City:
    name: str
    departures: list["Connection"] = field(default_factory=list)
    arrivals: list["Connection"]   = field(default_factory=list)

@dataclass
class Train:
    name: str
    connections: list["Connection"] = field(default_factory=list)

# connection object holds references to the other two objects above
# frozenset (immutable version of the set object) means that once it's created its 
# elements can't be modified. in this case, days is an immutable set of weekdays
@dataclass
class Connection:
    route_id: str
    dep_city: City
    arr_city: City
    dep_time: time
    arr_time: time
    days: FrozenSet[Weekday]
    first_class_eur: int 
    second_class_eur: int
    train: Train
    trip_minutes: int

# This is the method that will generate an alphanumeric ID for every trip
def generate_trip_id() -> str:
    letters = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TRP-{letters}"

@dataclass
class Trip:
    id: str = field(default_factory=generate_trip_id)
    reservations: list["Reservation"] = field(default_factory=list)
    connections: list["Connection"] = field(default_factory=list)

    # Add reservation - no duplicate check to avoid circular comparison
    def add_reservation(self, reservation: "Reservation") -> None:
        self.reservations.append(reservation)

    def _layover_difference_min(self, t1:time, t2:time) -> int: # returns layover duration in minutes (int)


    # Add layover rules #################################
        # Daytime: No layovers of more than 2 hours
        # Nighttime: No layovers of more than 30 minutes
        # At any time of day: At least 10 min to walk to the right stop and prepare tickets and suitcases
    def validate_layover(self) -> bool:
        for i in range(len(self.connections)-1):
            current_arr = self.connections[i].arr_time
            next_dept = self.connections[i+1].dep_time

            # calculate layover duration in min to make sure it respects layover rules
            layover_duration = self._layover_difference_min(current_arr,next_dept)

            # daytime layover rule: 2 hours or less
            if 6 <= next_dept.hour < 19: # daytime = between 6AM (incl) - 7PM (excl)
                if not (10 <= layover_duration <= 120):
                    return False
            if 19 <= next_dept.hour < 6: # nighttime = between 7PM (incl) - 6AM (excl)
                if not (10 <= layover_duration <= 30):
                    return False

@dataclass
class Traveller:
    first_name: str
    last_name: str
    age: int
    id: str
    reservations: list["Reservation"]   = field(default_factory=list)

    def add_reservation(self, reservation: "Reservation") -> None:
        # No duplicate check to avoid circular comparison issues
        self.reservations.append(reservation)

    def list_trips(self) -> list["Trip"]:
        return [r.trip for r in self.reservations]

@dataclass(eq=False)  # Disable automatic equality to prevent circular comparison
class Reservation:
    traveller: Traveller
    ticket: "Ticket"
    trip: Trip

    # Debugging method
    def summary(self) -> str:
        if not self.trip.reservations:
            route = "No route"
        else:
            connection = self.trip.connections[0]
            route = f"{connection.dep_city.name} → {connection.arr_city.name}"
        
        return (
            f"Reservation for {self.traveller.first_name} {self.traveller.last_name} "
            f"on trip {self.trip.id} ({route}) - ticket #: {self.ticket.id}"
         )

@dataclass(eq=False)  # Disable automatic equality to prevent circular comparison
class Ticket:
    reservation: "Reservation" = None  # Allow None to break circular dependency
    _id_counter: int = field(default=0, init=False, repr=False, compare=False)
    id: int = field(init=False)

    def __post_init__(self):
        type(self)._id_counter += 1
        self.id = type(self)._id_counter

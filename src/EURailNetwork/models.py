from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time
from typing import FrozenSet

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

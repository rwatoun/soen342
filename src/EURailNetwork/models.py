from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time
from typing import FrozenSet

Weekday = int  

@dataclass
class City:
    name: str
    departures: list["Connection"] = field(default_factory=list)
    arrivals: list["Connection"]   = field(default_factory=list)

@dataclass
class Train:
    name: str
    connections: list["Connection"] = field(default_factory=list)

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

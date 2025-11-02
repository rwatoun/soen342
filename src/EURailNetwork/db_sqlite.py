from __future__ import annotations
import sqlite3
from datetime import time
from typing import Iterable
from .models import City, Train, Connection, Traveller, Trip, Reservation, Ticket
from .registries import RailNetwork, BookingSystem
from .utils_time import parse_time, format_time


def connect(db_path: str = "eurail.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def migrate(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS City (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Train (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Connection (
        id INTEGER PRIMARY KEY,
        depCityId INTEGER NOT NULL,
        arrCityId INTEGER NOT NULL,
        trainId INTEGER NOT NULL,
        depTime TEXT NOT NULL,   
        arrTime TEXT NOT NULL,   
        routeId TEXT NOT NULL,
        tripMinutes INTEGER NOT NULL,
        firstClassEur INTEGER NOT NULL,
        secondClassEur INTEGER NOT NULL,
        FOREIGN KEY(depCityId)   REFERENCES City(id) ON DELETE RESTRICT,
        FOREIGN KEY(arrCityId)   REFERENCES City(id) ON DELETE RESTRICT,
        FOREIGN KEY(trainId)     REFERENCES Train(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS ConnectionDay (
        connectionId INTEGER NOT NULL,
        weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),
        PRIMARY KEY(connectionId, weekday),
        FOREIGN KEY(connectionId) REFERENCES Connection(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Traveller (
        id TEXT PRIMARY KEY,              
        firstName TEXT NOT NULL,
        lastName  TEXT NOT NULL,
        age INTEGER
    );

    CREATE TABLE IF NOT EXISTS Trip (
        id TEXT PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS TripConnection (
        tripId TEXT NOT NULL,
        seq INTEGER NOT NULL,
        connectionId INTEGER NOT NULL,
        PRIMARY KEY(tripId, seq),
        FOREIGN KEY(tripId) REFERENCES Trip(id) ON DELETE CASCADE,
        FOREIGN KEY(connectionId) REFERENCES Connection(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS Reservation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tripId TEXT NOT NULL,
        travellerId TEXT NOT NULL,
        seatClass TEXT CHECK(seatClass IN ('first','second')) DEFAULT 'second',
        ticketId INTEGER UNIQUE,  
        FOREIGN KEY(tripId) REFERENCES Trip(id) ON DELETE CASCADE,
        FOREIGN KEY(travellerId) REFERENCES Traveller(id) ON DELETE RESTRICT
    );
    """)
    conn.commit()


# this function checks if a row with the given id already exists and returns it
def _get_id(cur, table: str, name: str) -> int:
    cur.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
    row = cur.fetchone()
    return row[0] if row else None

# this function uses get_id to fetch for the id with the corresponding name. if it didn't find anything,
# it creates the record.  
def _ensure_named(cur, table: str, name: str) -> int:
    _id = _get_id(cur, table, name)
    if _id is not None:
        return _id
    cur.execute(f"INSERT INTO {table}(name) VALUES(?)", (name,))
    return cur.lastrowid


# this function takes all the static data in the network and saves them into db
def save_network(conn: sqlite3.Connection, net: RailNetwork) -> None:
    cur = conn.cursor()

    for c in net.cities.items:
        _ensure_named(cur, "City", c.name)  

    for t in net.trains.items:
        _ensure_named(cur, "Train", t.name)  

    # insert/update connections 
    for con in net.connections:
        dep_id   = _ensure_named(cur, "City",  con.dep_city.name)
        arr_id   = _ensure_named(cur, "City",  con.arr_city.name)
        train_id = _ensure_named(cur, "Train", con.train.name)

        dep_hhmm = (format_time(con.dep_time) if 'format_time' in globals() and format_time else format_time(con.dep_time))
        arr_hhmm = (format_time(con.arr_time) if 'format_time' in globals() and format_time else format_time(con.arr_time))

        # find existing row 
        cur.execute("""
            SELECT id FROM Connection
            WHERE routeId = ?
              AND depCityId = ?
              AND arrCityId = ?
              AND depTime = ?
              AND arrTime = ?
              AND trainId = ?
        """, (con.route_id, dep_id, arr_id, dep_hhmm, arr_hhmm, train_id))
        row = cur.fetchone()

        if row:
            conn_id = row[0]
            cur.execute("""
                UPDATE Connection
                   SET tripMinutes   = ?,
                       firstClassEur = ?,
                       secondClassEur= ?
                 WHERE id = ?
            """, (con.trip_minutes, con.first_class_eur, con.second_class_eur, conn_id))
        else:
            cur.execute("""
                INSERT INTO Connection(
                    depCityId, arrCityId, trainId,
                    depTime,  arrTime,   routeId,
                    tripMinutes, firstClassEur, secondClassEur
                ) VALUES (?,?,?,?,?,?,?,?,?)
            """, (dep_id, arr_id, train_id,
                  dep_hhmm, arr_hhmm, con.route_id,
                  con.trip_minutes, con.first_class_eur, con.second_class_eur))
            conn_id = cur.lastrowid

        # delete other weekdays for this connection
        cur.execute("DELETE FROM ConnectionDay WHERE connectionId = ?", (conn_id,))
        for d in sorted(con.days):
            cur.execute("INSERT INTO ConnectionDay(connectionId, weekday) VALUES (?,?)", (conn_id, d))

    conn.commit()

# this function saves the dynamic data (user’s trip, its connections, the travellers, and the reservations) into db
def save_trip(conn: sqlite3.Connection, trip: Trip) -> None:
    cur = conn.cursor()

    # trip header
    cur.execute("INSERT OR IGNORE INTO Trip(id) VALUES(?)", (trip.id,))

    # (re)write to avoid duplicates
    cur.execute("DELETE FROM TripConnection WHERE tripId = ?", (trip.id,))
    for idx, con in enumerate(trip.connections):
        dep_id   = _ensure_named(cur, "City",  con.dep_city.name)
        arr_id   = _ensure_named(cur, "City",  con.arr_city.name)
        train_id = _ensure_named(cur, "Train", con.train.name)

        dep_hhmm = (format_time(con.dep_time) if 'format_time' in globals() and format_time else format_time(con.dep_time))
        arr_hhmm = (format_time(con.arr_time) if 'format_time' in globals() and format_time else format_time(con.arr_time))

        # find the matching connection row
        cur.execute("""
            SELECT id FROM Connection
            WHERE routeId = ?
              AND depCityId = ?
              AND arrCityId = ?
              AND depTime = ?
              AND arrTime = ?
              AND trainId = ?
        """, (con.route_id, dep_id, arr_id, dep_hhmm, arr_hhmm, train_id))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Connection not present in DB; call save_network() first.")
        connection_id = row[0]

        cur.execute("""
            INSERT INTO TripConnection(tripId, seq, connectionId) VALUES (?,?,?)
        """, (trip.id, idx, connection_id))

    # travellers and reservations and ticketId
    for res in trip.reservations:
        t = res.traveller
        cur.execute("""
            INSERT OR IGNORE INTO Traveller(id, firstName, lastName, age)
            VALUES (?,?,?,?)
        """, (t.id, t.first_name, t.last_name, t.age))

        seat_cls = getattr(res, "seat_class", "second")
        cur.execute("""
            INSERT INTO Reservation(tripId, travellerId, seatClass, ticketId)
            VALUES (?,?,?,?)
        """, (trip.id, t.id, seat_cls, res.ticket.id))

    conn.commit()

# this function loads all the saved trips, travellers, etc from db and rebuilds them as python objects 
def load_trips(conn: sqlite3.Connection, system: BookingSystem, net: RailNetwork) -> None:
    """
    Recreate in-memory trips/travellers/reservations/tickets and link to existing network connections.
    """
    cur = conn.cursor()

    # travellers
    cur.execute("SELECT id, firstName, lastName, age FROM Traveller")
    by_id: dict[str, Traveller] = {}
    for tid, fn, ln, age in cur.fetchall():
        trav = (system.travellers.get_or_create(first_name=fn, last_name=ln, age=age, id=tid)
                if hasattr(system.travellers, "get_or_create")
                else Traveller(first_name=fn, last_name=ln, age=age, id=tid))
        by_id[tid] = trav

    # trips
    cur.execute("SELECT id FROM Trip")
    for (trip_id,) in cur.fetchall():
        trip = Trip(id=trip_id, connections=[], reservations=[])

        # ordered trip segments
        cur.execute("""
            SELECT
                c.routeId,
                dc.name,         -- dep city name
                ac.name,         -- arr city name
                c.depTime,
                c.arrTime,
                t.name           -- train name
            FROM TripConnection tc
            JOIN Connection c  ON c.id  = tc.connectionId
            JOIN City dc       ON dc.id = c.depCityId
            JOIN City ac       ON ac.id = c.arrCityId
            JOIN Train t       ON t.id  = c.trainId
            WHERE tc.tripId = ?
            ORDER BY tc.seq ASC
        """, (trip_id,))
        rows = cur.fetchall()

        # map back to existing connection objects in memory
        for route_id, dep, arr, dep_t, arr_t, train_name in rows:
            match = next((
                c for c in net.connections
                if c.route_id == route_id
                and c.dep_city.name == dep
                and c.arr_city.name == arr
                and ((format_time(c.dep_time) if 'format_time' in globals() and format_time else format_time(c.dep_time)) == dep_t)
                and ((format_time(c.arr_time) if 'format_time' in globals() and format_time else format_time(c.arr_time)) == arr_t)
                and c.train.name == train_name
            ), None)
            if match is not None:
                trip.connections.append(match)

        # reservations
        cur.execute("""
            SELECT travellerId, seatClass, ticketId
            FROM Reservation
            WHERE tripId = ?
        """, (trip_id,))
        for trav_id, seat_cls, ticket_id in cur.fetchall():
            traveller = by_id.get(trav_id)
            if traveller is None:
                continue
            ticket = Ticket(reservation=None)
            ticket.id = ticket_id
            res = Reservation(traveller=traveller, ticket=ticket, trip=trip)
            if hasattr(res, "seat_class"):
                setattr(res, "seat_class", seat_cls)
            ticket.reservation = res
            trip.add_reservation(res)
            traveller.add_reservation(res)

        system.trips.items.append(trip)
        system.trips.by_id[trip.id] = trip

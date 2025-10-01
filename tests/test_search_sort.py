import textwrap
from pathlib import Path

import pytest

from EURailNetwork.loader import read_raw_csv, build_network_from_df
from EURailNetwork.registries import RailNetwork  

# this method creates a small csv that has connections which cover most cases
# it also returns the path to that temporary csv file
def _make_csv(tmp_path: Path) -> str:
    csv = textwrap.dedent("""\
        Route ID,Departure City,Arrival City,Departure Time,Arrival Time,Train Type,Days of Operation,First Class ticket rate (in euro),Second Class ticket rate (in euro)
        R001,Paris,Lyon,08:00,10:00,TGV,Mon|Tue|Wed,100,50
        R002,Paris,Lyon,09:15,10:30,RegioExpress,Daily,80,40
        R003,Paris,Lyon,22:30,06:10 (+1d),Nightjet,Daily,70,30
        R004,Lyon,Paris,11:00,13:00,TGV,Mon|Tue,100,50
        R005,Paris,Berlin,07:00,13:00,ICE,Mon|Wed|Fri,150,90
        R006,Paris,Lyon,08:00,09:00,InterCity,Mon|Tue,120,60
    """)
    p = tmp_path / "routes.csv"
    p.write_text(csv, encoding="utf-8")
    return str(p)

# this method creates one network per test and reads the small csv
# it also returns that RailNetwork Object
@pytest.fixture()
def net(tmp_path: Path) -> RailNetwork:
    path = _make_csv(tmp_path)
    df = read_raw_csv(path)
    return build_network_from_df(df)  


# SEARCH TESTS

def test_find_direct_all_paris_lyon(net: RailNetwork):
    conns = net.find_direct("Paris", "Lyon")
    got = {c.route_id for c in conns}
    assert got == {"R001", "R002", "R003", "R006"}


def test_find_direct_case_insensitive(net: RailNetwork):
    conns = net.find_direct("paris", "LYON")
    got = {c.route_id for c in conns}
    assert got == {"R001", "R002", "R003", "R006"}


def test_find_direct_filter_by_weekday_monday(net: RailNetwork):
    monday = 0
    conns = net.find_direct("Paris", "Lyon", weekday=monday)
    got = {c.route_id for c in conns}
    assert got == {"R001", "R002", "R003", "R006"}


def test_find_direct_no_match_returns_empty(net: RailNetwork):
    assert net.find_direct("Berlin", "Paris") == []


# SORTING TESTS

def test_sort_by_duration_ascending(net: RailNetwork):
    paris_lyon = net.find_direct("Paris", "Lyon")
    ordered = net.sort_connections(paris_lyon, by="trip_minutes", ascending=True)
    assert [c.route_id for c in ordered] == ["R006", "R002", "R001", "R003"]


def test_sort_by_duration_descending(net: RailNetwork):
    paris_lyon = net.find_direct("Paris", "Lyon")
    ordered = net.sort_connections(paris_lyon, by="trip_minutes", ascending=False)
    assert [c.route_id for c in ordered] == ["R003", "R001", "R002", "R006"]


def test_sort_by_second_class_price_ascending(net: RailNetwork):
    paris_lyon = net.find_direct("Paris", "Lyon")
    ordered = net.sort_connections(paris_lyon, by="price", ascending=True, price_class="second")
    assert [c.route_id for c in ordered] == ["R003", "R002", "R001", "R006"]


def test_sort_by_first_class_price_descending(net: RailNetwork):
    paris_lyon = net.find_direct("Paris", "Lyon")
    ordered = net.sort_connections(paris_lyon, by="price", ascending=False, price_class="first")
    assert [c.route_id for c in ordered] == ["R006", "R001", "R002", "R003"]

# this method outlines how we break ties when we sort (based on departure time and route id)
def test_sort_ties_break_by_dep_time_then_route_id(net: RailNetwork):
    paris_lyon = net.find_direct("Paris", "Lyon")
    ordered = net.sort_connections(paris_lyon, by="trip_minutes", ascending=True)
    assert ordered[0].route_id == "R006"

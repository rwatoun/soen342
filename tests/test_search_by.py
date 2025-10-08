import textwrap
from pathlib import Path
from datetime import time

import pytest

from EURailNetwork.loader import read_raw_csv, build_network_from_df
from EURailNetwork.registries import RailNetwork 

# Creating a separate rail network for the tests
@pytest.fixture()
def network_test() -> RailNetwork:
    path_to_csv = "data/eu_rail_network.csv"
    new_df = read_raw_csv(path_to_csv)
    return build_network_from_df(new_df)

# Test cases - Trying to cover every feature and every case -----------------------------

# 1. Testing case-sensitivity when filtering (on city)
def test_find_direct_case_sensitive(network_test):
    # Testing when entire input is lowercase
    c_lower = network_test.find_direct("paris", "london")
    # Testing when entire input is uppercase
    c_upper = network_test.find_direct("PARIS", "LONDON")
    # Testing when entire input is a random mix of lowercase and uppercase
    c_mix = network_test.find_direct("pAriS", "lOnDon")

    # Length of each result should be the same, because we are looking for the same connection(s)
    assert len(c_lower) == len(c_upper) == len(c_mix)
    
    # route_id of each returned connection should be the same for each case
    if c_lower:
        ids_lower = {c.route_id for c in c_lower}
        ids_upper = {c.route_id for c in c_upper}
        ids_mixed = {c.route_id for c in c_mix}
        assert ids_lower == ids_upper == ids_mixed

# 2. Testing substring search when filtering (on city)
def test_find_direct_substring(network_test: RailNetwork):
    c_full = network_test.find_direct("Paris", "London")
    c_substring = network_test.find_direct("Par", "ondon")

    assert len(c_full) == len(c_substring)

    if c_full:
        ids_full = {c.route_id for c in c_full}
        ids_substring = {c.route_id for c in c_substring}
        assert ids_full == ids_substring

# 3. Testing weekday filtering
def test_find_direct_weekday_filter(network_test: RailNetwork):
    # Testing on Monday (subject 0)
    c_monday = network_test.find_direct("Padua", "Venice", weekday=0)

    # To complete...

# 4. Testing no results - Nonexistent cities
def test_find_direct_nonexistent_trip(network_test: RailNetwork):
    c_nothing = network_test.find_direct("Atlantis", "Texas")
    assert c_nothing == [] # Should return an empty set because passed wrong city input

# 5. Testing no results - Passing same city for departure and arrival city
def test_find_direct_same_city_inexistent_trip(network_test: RailNetwork):
    c_nothing = network_test.find_direct("London", "London")
    assert c_nothing == [] # Should return an empty set because there can't be a trip from one city to the same city

# 6.1 Testing max first class price filtering
def test_find_direct_max_first_price_filter(network_test: RailNetwork):
    max_first_price = 90
    results = network_test.search_connections(
        depart_city="Paris",
        max_first_class_price=max_first_price,
        sort_by="first_class_eur",
        ascending=True
    )
    
    # Verify all results are within price limit
    for c in results:
        assert c.first_class_eur <= max_first_price
        assert "paris" in c.dep_city.name.lower()

# 6.2 Testing min first class price filtering
def test_find_direct_min_first_price_filter(network_test: RailNetwork):
    min_first_price = 90
    results = network_test.search_connections(
        depart_city="Paris",
        min_first_class_price=min_first_price,
        sort_by="first_class_eur",
        ascending=True
    )
    
    # Verify all results are within price limit
    for c in results:
        assert c.first_class_eur <= min_first_price
        assert "paris" in c.dep_city.name.lower()

# 6.3 Testing max second class price filtering
def test_find_direct_max_second_price_filter(network_test: RailNetwork):
    max_second_price = 90
    results = network_test.search_connections(
        depart_city="Paris",
        min_first_class_price=max_second_price,
        sort_by="second_class_eur",
        ascending=True
    )
    
    # Verify all results are within price limit
    for c in results:
        assert c.second_class_eur <= max_second_price
        assert "paris" in c.dep_city.name.lower()

# 6.4 Testing min second class price filtering
def test_find_direct_min_second_price_filter(network_test: RailNetwork):
    min_second_price = 90
    results = network_test.search_connections(
        depart_city="Paris",
        min_first_class_price=min_second_price,
        sort_by="second_class_eur",
        ascending=True
    )
    
    # Verify all results are within price limit
    for c in results:
        assert c.first_class_eur <= min_second_price
        assert "paris" in c.dep_city.name.lower()
import pandas as pd
from .models import Connection
from .registries import RailNetwork
from .utils_time import parse_time_with_offset, duration_minutes_with_offset
from .schema import parse_days, parse_price_int

COLS = [
    "route_id","departure_city","arrival_city","departure_time","arrival_time",
    "train_type","days_of_operation","first_class_eur","second_class_eur"
]

def read_raw_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig", sep=None, engine="python")
    aliases = {
        "route_id": "route_id",
    "departure_city": "departure_city",
    "arrival_city": "arrival_city",
    "departure_time": "departure_time",
    "arrival_time": "arrival_time",
    "train_type": "train_type",
    "days_of_operation": "days_of_operation",
    "second_class_ticket_rate_(in_euro)":"second_class_eur",
    "first_class_ticket_rate_(in_euro)":"first_class_eur"
    }
    df = df.rename(columns={c: c.strip().lower().replace(" ", "_") for c in df.columns})
    for k,v in list(aliases.items()):
        if k in df.columns and v not in df.columns:
            df = df.rename(columns={k:v})
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found={list(df.columns)}")
    df = df[COLS].apply(lambda s: s.str.strip())
    return df

def build_network_from_df(df: pd.DataFrame) -> RailNetwork:
    g = RailNetwork()
    for i, row in df.iterrows():
        dep_city = g.cities.get_or_create(row["departure_city"])
        arr_city = g.cities.get_or_create(row["arrival_city"])
        train    = g.trains.get_or_create(row["train_type"])

        dep_t, dep_off = parse_time_with_offset(row["departure_time"])
        arr_t, arr_off = parse_time_with_offset(row["arrival_time"])
        if dep_off not in (0,):  # usually departure won't carry +Nd; treat as data issue if it does
            raise ValueError(f"Row {i}: departure_time has unexpected day offset '(+{dep_off}d)'")
        days  = parse_days(row["days_of_operation"])
        p1    = parse_price_int(row["first_class_eur"])
        p2    = parse_price_int(row["second_class_eur"])
        dur   = duration_minutes_with_offset(dep_t, arr_t, arr_day_offset=arr_off)

        if dep_city is arr_city:
            raise ValueError(f"Row {i}: departure equals arrival ({dep_city.name})")

        conn = Connection(
            route_id=row["route_id"],
            dep_city=dep_city,
            arr_city=arr_city,
            dep_time=dep_t,
            arr_time=arr_t,
            days=days,
            first_class_eur=p1,
            second_class_eur=p2,
            train=train,
            trip_minutes=dur,
        )
        g.add_connection(conn)
    return g

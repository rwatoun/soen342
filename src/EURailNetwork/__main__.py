import argparse
from .loader import read_raw_csv, build_network_from_df
from .inspectors import print_summary, print_city, print_train

def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    p.add_argument("--head", type=int, default=5)
    p.add_argument("--summary", action="store_true")
    p.add_argument("--city")
    p.add_argument("--train")
    args = p.parse_args()
    args = p.parse_args()

    df = read_raw_csv(args.csv_path)
    g = build_network_from_df(df)

    if args.summary:
        print_summary(g, top=args.head)
    if args.city:
        print_city(g, args.city, limit=args.head)
    if args.train:
        print_train(g, args.train, limit=args.head)
    if not (args.summary or args.city or args.train):
        # default preview of first N connections
        print(f"Parsed {len(g.connections)} connections, {len(g.cities.items)} cities, {len(g.trains.items)} trains\n")
        for c in g.connections[:args.head]:
            print(f"{c.route_id}: {c.dep_city.name} {c.dep_time} → {c.arr_city.name} {c.arr_time} ({c.trip_minutes} min) [{c.train.name}]")

if __name__ == "__main__":
    main()


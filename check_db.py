"""
Script to verify what's saved in the eurail.db database
Run: python check_db.py
"""
import sqlite3
from colorama import Fore, Style, init

init(autoreset=True)

def check_database(db_path="eurail.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(Fore.CYAN + "=" * 70)
    print("DATABASE CONTENTS CHECK")
    print("=" * 70 + Style.RESET_ALL)
    
    # Check all tables
    print(Fore.YELLOW + "\nTable Counts:" + Style.RESET_ALL)
    tables = ['City', 'Train', 'Connection', 'Traveller', 'Trip', 'Reservation']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:15} {count:5} records")
    
    # Show travellers
    print(Fore.YELLOW + "\nTravellers:" + Style.RESET_ALL)
    cursor.execute("SELECT id, firstName, lastName, age FROM Traveller")
    travellers = cursor.fetchall()
    if travellers:
        for tid, first, last, age in travellers:
            full_name = f"{first} {last}"
            print(f"  ID: {tid:<15} Name: {full_name:<30} Age: {age}")
    else:
        print(Fore.RED + "  No travellers found" + Style.RESET_ALL)
    
    # Show trips
    print(Fore.YELLOW + "\nTrips:" + Style.RESET_ALL)
    cursor.execute("SELECT id FROM Trip")
    trips = cursor.fetchall()
    if trips:
        for (trip_id,) in trips:
            print(f"\n  Trip ID: {Fore.GREEN}{trip_id}{Style.RESET_ALL}")
            
            # Get connections for this trip
            cursor.execute("""
                SELECT dc.name, ac.name, c.depTime, c.arrTime, t.name
                FROM TripConnection tc
                JOIN Connection c ON tc.connectionId = c.id
                JOIN City dc ON c.depCityId = dc.id
                JOIN City ac ON c.arrCityId = ac.id
                JOIN Train t ON c.trainId = t.id
                WHERE tc.tripId = ?
                ORDER BY tc.seq
            """, (trip_id,))
            connections = cursor.fetchall()
            for dep, arr, dep_time, arr_time, train in connections:
                print(f"    Route: {dep} → {arr}")
                print(f"    Time: {dep_time} - {arr_time} | Train: {train}")
            
            # Get travellers for this trip
            cursor.execute("""
                SELECT tr.firstName, tr.lastName, r.ticketId
                FROM Reservation r
                JOIN Traveller tr ON r.travellerId = tr.id
                WHERE r.tripId = ?
            """, (trip_id,))
            reservations = cursor.fetchall()
            print(f"    Travellers:")
            for first, last, ticket in reservations:
                print(f"      - {first} {last} (Ticket #{ticket})")
    else:
        print(Fore.RED + "  No trips found" + Style.RESET_ALL)
    
    # Show reservations summary
    print(Fore.YELLOW + "\nReservations Summary:" + Style.RESET_ALL)
    cursor.execute("""
        SELECT 
            r.id,
            t.id as TripID,
            tr.firstName || ' ' || tr.lastName as Name,
            r.seatClass,
            r.ticketId
        FROM Reservation r
        JOIN Trip t ON r.tripId = t.id
        JOIN Traveller tr ON r.travellerId = tr.id
    """)
    reservations = cursor.fetchall()
    if reservations:
        for res_id, trip_id, name, seat, ticket in reservations:
            print(f"  Reservation #{res_id}: {name} | Trip: {trip_id} | Seat: {seat} | Ticket: {ticket}")
    else:
        print(Fore.RED + "  No reservations found" + Style.RESET_ALL)
    
    print(Fore.CYAN + "\n" + "=" * 70 + Style.RESET_ALL)
    conn.close()

if __name__ == "__main__":
    try:
        check_database()
    except sqlite3.OperationalError as e:
        print(Fore.RED + f"Error: {e}")
        print("Make sure eurail.db exists in the current directory" + Style.RESET_ALL)

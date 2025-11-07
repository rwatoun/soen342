-- SQL queries to verify data in eurail.db
-- Run these in SQLite CLI: sqlite3 eurail.db

-- ===== Check all tables exist =====
.tables

-- ===== Count records in each table =====
SELECT 'Cities' as TableName, COUNT(*) as Count FROM City
UNION ALL
SELECT 'Trains', COUNT(*) FROM Train
UNION ALL
SELECT 'Connections', COUNT(*) FROM Connection
UNION ALL
SELECT 'Travellers', COUNT(*) FROM Traveller
UNION ALL
SELECT 'Trips', COUNT(*) FROM Trip
UNION ALL
SELECT 'Reservations', COUNT(*) FROM Reservation;

-- ===== View all travellers =====
SELECT * FROM Traveller;

-- ===== View all trips =====
SELECT * FROM Trip;

-- ===== View all reservations with traveller names =====
SELECT 
    r.id as ReservationID,
    t.id as TripID,
    tr.firstName || ' ' || tr.lastName as TravellerName,
    tr.id as TravellerID,
    r.seatClass,
    r.ticketId
FROM Reservation r
JOIN Trip t ON r.tripId = t.id
JOIN Traveller tr ON r.travellerId = tr.id;

-- ===== View trip details (connections) =====
SELECT 
    t.id as TripID,
    tc.seq as Sequence,
    dc.name as DepartureCity,
    ac.name as ArrivalCity,
    c.depTime as DepartureTime,
    c.arrTime as ArrivalTime,
    tr.name as TrainName
FROM Trip t
JOIN TripConnection tc ON t.id = tc.tripId
JOIN Connection c ON tc.connectionId = c.id
JOIN City dc ON c.depCityId = dc.id
JOIN City ac ON c.arrCityId = ac.id
JOIN Train tr ON c.trainId = tr.id
ORDER BY t.id, tc.seq;

-- ===== View complete trip information =====
SELECT 
    t.id as TripID,
    traveller.firstName || ' ' || traveller.lastName as Traveller,
    dc.name || ' → ' || ac.name as Route,
    c.depTime || ' - ' || c.arrTime as Times
FROM Trip t
JOIN Reservation r ON t.id = r.tripId
JOIN Traveller traveller ON r.travellerId = traveller.id
JOIN TripConnection tc ON t.id = tc.tripId
JOIN Connection c ON tc.connectionId = c.id
JOIN City dc ON c.depCityId = dc.id
JOIN City ac ON c.arrCityId = ac.id
ORDER BY t.id;

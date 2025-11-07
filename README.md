# SOEN 342 (II) - EU Rail Network

## Team Members
| Full Name      | Username     | Student ID |
| -------------- | ------------ | ---------- |
| Marwa Hammani  | @rwatoun     | 40289362   |
| Justyne Phan   | @JustynePhan | 40278509   |
| Elif Sag Sesen | @elif5446    | 40283343   |


## Requirements and Commands
### Running the Program
Must have Python installed.  
Depending on your Python version, you might have to replace the python command with python3.  
Colorama library (for colored CLI output).  

After cloning the repository:  
```python -m venv .venv```  
```pip install -e .```  
```pip install colorama```  
```python -m EURailNetwork data/eu_rail_network.csv```

This will launch the interactive menu where you can view the network summary, search for connections, view city information, or view train details.  

### Running the Tests
To run **tests**: ```pytest -v```  

### Checking Database Contents
**Option 1: Using Python script**  
```python check_db.py```

This will display:
- Count of records in each table
- List of all travellers
- All trips with their connections and routes
- Reservations summary

**Option 2: Using SQLite CLI**  
Open database: ```sqlite3 eurail.db```  
View tables: ```.tables```  
View schema structure: ```.schema TableName```

**Some SQL Queries:**
```sql
-- View all travellers
SELECT * FROM Traveller;

-- View all trips with traveller information
SELECT t.id, tr.firstName, tr.lastName, tr.age, r.ticketId 
FROM Trip t 
JOIN Reservation r ON t.id = r.tripId 
JOIN Traveller tr ON r.travellerId = tr.id;

-- View trip routes
SELECT t.id as TripID, dc.name || ' → ' || ac.name as Route, c.depTime, c.arrTime
FROM Trip t
JOIN TripConnection tc ON t.id = tc.tripId
JOIN Connection c ON tc.connectionId = c.id
JOIN City dc ON c.depCityId = dc.id
JOIN City ac ON c.arrCityId = ac.id
ORDER BY t.id, tc.seq;
```

For more queries, see `check_database.sql` file. 



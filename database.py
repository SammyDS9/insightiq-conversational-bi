import sqlite3
from pathlib import Path
import random
from datetime import date, timedelta

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'operations.db'


def initialize(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return db_path
    rng = random.Random(42)
    with sqlite3.connect(db_path) as con:
        con.executescript('''
        CREATE TABLE facilities (facility_id INTEGER PRIMARY KEY, facility_name TEXT NOT NULL, region TEXT NOT NULL);
        CREATE TABLE daily_operations (facility_id INTEGER NOT NULL, service_date TEXT NOT NULL, visits INTEGER NOT NULL, admissions INTEGER NOT NULL, staffed_hours REAL NOT NULL, expenses REAL NOT NULL, avg_wait_minutes REAL NOT NULL, FOREIGN KEY(facility_id) REFERENCES facilities(facility_id));
        ''')
        con.executemany('INSERT INTO facilities VALUES (?,?,?)', [(1,'North Campus','North'),(2,'South Campus','South'),(3,'Central Campus','Central'),(4,'West Campus','West')])
        start = date(2025, 1, 1)
        rows=[]
        for d in range(365):
            day = start + timedelta(days=d)
            for facility in range(1,5):
                visits = max(10, int(55 + facility*13 + (d%7)*2 + rng.gauss(0,9)))
                admissions = int(visits * rng.uniform(.12,.24))
                hours = round(visits * rng.uniform(1.4,2.2),1)
                expenses = round(hours * rng.uniform(40,62),2)
                wait = round(max(5, rng.gauss(32+facility*3,7)),1)
                rows.append((facility,day.isoformat(),visits,admissions,hours,expenses,wait))
        con.executemany('INSERT INTO daily_operations VALUES (?,?,?,?,?,?,?)', rows)
    return db_path


def schema_text():
    return '''SQLite tables:\nfacilities(facility_id INTEGER PRIMARY KEY, facility_name TEXT, region TEXT)\ndaily_operations(facility_id INTEGER, service_date TEXT [YYYY-MM-DD], visits INTEGER, admissions INTEGER, staffed_hours REAL, expenses REAL, avg_wait_minutes REAL)\nJOIN ON facilities.facility_id = daily_operations.facility_id. Data is SYNTHETIC. Use SQLite SQL only.'''

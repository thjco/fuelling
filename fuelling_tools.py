import sqlite3
import json
import pandas as pd
from datetime import datetime


DB_FILE = "fuelling.db"
EXAMPLE_FILE = "fuelling-examples.json"

ENSURE_FILLING_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS filling (
        id integer PRIMARY KEY,
        fdate datetime NOT NULL,
        evaluate tinyint(1) NOT NULL DEFAULT '1',
        quantity float NOT NULL,
        full tinyint(1) NOT NULL DEFAULT '1',
        price float NOT NULL,
        mileage float NOT NULL,
        station varchar(32) NOT NULL,
        comment varchar(128) NOT NULL
    );
"""

DROP_FILLING_TABLE = """
    DROP TABLE IF EXISTS filling;
"""

FILLING_INSERT_SQL = """
    INSERT INTO filling (fdate, evaluate, quantity, full, price, mileage, station, comment)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?);
"""

FILLING_SELECT_SQL = """
    SELECT id, fdate, evaluate, quantity, full, price, mileage, station, comment FROM filling ORDER BY fdate ASC;
"""


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def ensure_tables(conn):
    cur = conn.cursor()
    cur.execute(ENSURE_FILLING_TABLE_SQL)
    conn.commit()


def drop_tables():
    conn = create_connection(DB_FILE)
    cur = conn.cursor()
    cur.execute(DROP_FILLING_TABLE)
    conn.commit()
    conn.close()


def create_entry(conn, entry):
    """Put a new entry into the database
    :param conn: connection object
    :param entry: entry to be stored
    """
    values = (entry["fdate"], entry["evaluate"], entry["quantity"], entry["full"],
              entry["price"], entry["mileage"], entry["station"], entry["comment"])
    cur = conn.cursor()
    cur.execute(FILLING_INSERT_SQL, values)
    conn.commit()


def select_all_entries(conn):
    """Read all entries from the database table
    :param: connection object
    :return: pd.DataFrame
    """
    cur = conn.cursor()
    cur.execute(FILLING_SELECT_SQL)
    rows = cur.fetchall()

    columns = "id fdate evaluate quantity full price mileage station comment".split()
    df = pd.DataFrame(rows, columns=columns).set_index("id")
    df["evaluate"] = df.evaluate.astype(bool)
    df["full"] = df.full.astype(bool)
    df["mileage"] = df.mileage.astype(int)
    return df


def get_default_entry():
    data = {"fdate": datetime.today(), "quantity": 0.0, "full": True, "price": 0.0,
            "mileage": 0, "station": "", "evaluate": True, "comment": ""}
    return pd.Series(data=data)


def set_example_data():
    with open(EXAMPLE_FILE) as f:
        entries = json.load(f)
    entries = pd.DataFrame(entries).sort_values("fdate")

    drop_tables()

    conn = create_connection(DB_FILE)
    ensure_tables(conn)

    for _, entry in entries.iterrows():
        create_entry(conn, entry)

    conn.close()

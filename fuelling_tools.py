import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date


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


def get_insights(entries):
    df = entries.copy()

    df["consumption"] = None
    df["price_per_unit"] = None
    df["distance_per_day"] = None


    quantity_sum = 0.
    last_mileage_full = None
    last_mileage_entry = None
    last_date = None

    for idx, row in df.iterrows():
        quantity = row["quantity"]
        mileage = row["mileage"]

        # convert string to datetime object
        fdate = datetime.strptime(row["fdate"], "%Y-%m-%d %H:%M:%S")
        fdate = fdate.date()

        if quantity != 0:
            price_per_unit = row["price"] / quantity
            df.loc[idx, "price_per_unit"] = round(price_per_unit, 3)

        if last_date and last_mileage_entry:
            # calc mean distance only for different subsequent days
            days = (fdate - last_date).days
            if days != 0:
                distance_per_day = (mileage - last_mileage_entry) / days
                distance_per_day = int(distance_per_day)
                if distance_per_day > 0:
                    df.loc[idx, "distance_per_day"] = distance_per_day

        last_date = fdate
        last_mileage_entry = mileage

        quantity_sum += quantity

        if row["evaluate"] and last_mileage_full:
            if row["full"]:
                dm = mileage - last_mileage_full
                if dm != 0:
                    consumption = quantity_sum / dm * 100.0
                    if consumption > 0.:
                        df.loc[idx, "consumption"] = round(consumption, 1)

                    quantity_sum = 0.
                last_mileage_full = mileage
        else:
            quantity_sum = 0.
            last_mileage_full = mileage

    return df

def consumption_plot(df):
    consumption = df[["fdate", "consumption"]].dropna()
    min_date = datetime.strptime(consumption.fdate.min(), "%Y-%m-%d %H:%M:%S").date()
    max_date = datetime.strptime(consumption.fdate.max(), "%Y-%m-%d %H:%M:%S").date()
    xticks = pd.date_range(min_date, max_date, periods=20)
    fig, ax = plt.subplots()
    consumption["consumption"].plot(ax=ax)
    ax.set_xticklabels([x.strftime('%Y-%m-%d') for x in xticks])
    plt.xticks(rotation=60)
    return fig

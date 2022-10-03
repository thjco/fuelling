import streamlit as st
import matplotlib.pyplot as plt
from fuelling_tools import *


# next steps
# - additional tabs
#   - graphische auswertung: preisentwicklung, verbrauch, fahrleistung
#   - tabelle (mit z.B. Preis/Liter; Export/Import-Möglichkeit)
# - Import-Möglichkeit auch bel leerer Tabelle, initial


st.title("Tankwart")

with st.sidebar:
    if st.button("Daten löschen"):
        drop_tables()

    if st.button("Beispieldaten"):
        set_example_data()

conn = create_connection(DB_FILE)
ensure_tables(conn)

entries = select_all_entries(conn)


def get_default_entry():
    data = {"fdate": datetime.now(), "quantity": 0.0, "full": True, "price": 0.0,
            "mileage": 0, "station": "", "evaluate": True, "comment": ""}
    return pd.Series(data=data)


def entry_input(data):
    with st.form("input"):

        # tankdatum und uhrzeit
        fdate_date = st.date_input("Tankdatum", value=data.fdate.date()) # value="2022/10/02") #
        fdate_time = st.time_input("Tankzeit", value=data.fdate.time())
        fdate = datetime.combine(fdate_date, fdate_time)
        fdate = fdate.replace(microsecond=0)
        fdate = str(fdate)

        # menge
        quantity = st.number_input("Menge", min_value=0.0, step=0.01, value=data.quantity)

        # vollgetankt, teilbetankung
        full = st.radio("Füllstand", ("vollgetankt", "teilbetankt"), index=(1-data.full), horizontal=True)

        # preis
        price = st.number_input("Preis", min_value=0.0, step=0.01, value=data.price)

        # km-Stand
        mileage = st.number_input("km-Stand", min_value=0, value=data.mileage)

        # Station
        station = st.text_input("Station", value=data.station, max_chars=32)

        # Verbrauch berechnen
        evaluate = st.radio("Konsistenz", ("Verbrauch berechnen", "Keine Auswertung"), index=(1-data.evaluate), horizontal=True)

        # Kommentar
        comment = st.text_area("Kommentar", value=data.comment, max_chars=128)

        submitted = st.form_submit_button("Absenden")
        if submitted:
            # TODO Close connection at this point?
            data = { "fdate": fdate, "quantity": quantity, "full": full=="vollgetankt", "price": price,
                    "mileage": mileage, "station": station, "evaluate": evaluate=="Verbrauch berechnen", "comment": comment }
            return pd.Series(data=data)
        else:
            return None


default_entry = get_default_entry()
entry = entry_input(default_entry)

if isinstance(entry, pd.Series):
    create_entry(conn, entry)
    entries = select_all_entries(conn)

insights = get_insights(entries)

consumption = insights[["fdate", "consumption"]].dropna()
if consumption.shape[0] > 0:
    fig, ax = plt.subplots()
    ax.plot(consumption["consumption"], label="Verbrauch", color="b", marker="o", linewidth=2, markersize=6)
    plt.legend()
    st.pyplot(fig)

price_per_unit = insights[["fdate", "price_per_unit"]].dropna()
if price_per_unit.shape[0] > 0:
    fig, ax = plt.subplots()
    ax.plot(price_per_unit["price_per_unit"], label="Literpreis", color="r", marker="s", linewidth=2, markersize=6)
    plt.legend()
    st.pyplot(fig)

distance_per_day = insights[["fdate", "distance_per_day"]].dropna()
if distance_per_day.shape[0] > 0:
    fig, ax = plt.subplots()
    ax.plot(distance_per_day["distance_per_day"], label="mittlere Tagesdistanz", color="k", marker="p", linewidth=2, markersize=6)
    plt.legend()
    st.pyplot(fig)

st.dataframe(insights.iloc[::-1])

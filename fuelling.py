import streamlit as st
from fuelling_tools import *


# next steps
# - additional tabs
#   - graphische auswertung: preisentwicklung, verbrauch, fahrleistung
#   - tabelle (mit z.B. Preis/Liter; Export/Import-Möglichkeit)
# - Import-Möglichkeit auch bel leerer Tabelle, initial


st.set_page_config(layout="wide")
st.title("Fuelling")


@st.cache
def get_entries():
    conn = create_connection(DB_FILE)
    ensure_tables(conn)
    df = select_all_entries(conn)
    return df

if "entries" not in st.session_state:
    st.session_state.entries = get_entries()


def get_default_entry():
    data = {"fdate": datetime.today(), "quantity": 0.0, "full": True, "price": 0.0,
            "mileage": 0, "station": "", "evaluate": True, "comment": ""}
    return pd.Series(data=data)


def entry_input(data):
    with st.form("input"):

        # tankdatum
        fdate = st.date_input("Tankdatum", value=data.fdate)

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
            data = { "fdate": fdate, "quantity": quantity, "full": full=="vollgetankt", "price": price,
                    "mileage": mileage, "station": station, "evaluate": evaluate=="Verbrauch berechnen", "comment": comment }
            return pd.Series(data=data)
        else:
            return None


default_entry = get_default_entry()
entry = entry_input(default_entry)


if isinstance(entry, pd.Series):
    entry = pd.DataFrame(entry)
    st.session_state.entries = pd.concat([st.session_state.entries, entry.T], axis=0, ignore_index=True)
else:
    print("no entry")

#print(st.session_state.entries)
#st.write(entries)



st.dataframe(st.session_state.entries.iloc[::-1])
#entries.shape

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import psycopg2
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Use environment variables for database connection
db_user = os.getenv('DB_USER', 'flatbot_db')
db_password = os.getenv('DB_PASSWORD', 'DDQ9Gv7IABBqu1WrTMZt')
db_host = os.getenv('DB_HOST', 'flatbot-db-server.postgres.database.azure.com')
db_name = os.getenv('DB_NAME', 'flatbotdb')

# Format the username correctly
formatted_user = f'{db_user}@{db_host.split(".")[0]}'


def load_data():
    connection = psycopg2.connect(
        database=db_name,
        user=formatted_user,  # Use the correct username format
        password=db_password,
        host=db_host,
        port="5432",
        sslmode='require'
    )
    query = "SELECT * FROM results"  # Replace with your actual query
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df

def filter_data(df, max_price, min_size, min_rooms, selected_cities, selected_neighbourhoods):
    filtered_df = df[
        (df["price"] <= max_price) &
        (df["size"] >= min_size) &
        (df["rooms"] >= min_rooms) &
        df["city"].isin(selected_cities) &
        df["neighbourhood"].isin(selected_neighbourhoods)
    ]
    return filtered_df

def store_user_settings(user_id, user_settings):
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    connection = psycopg2.connect(database=db_name, user=formatted_user, password=db_password, host=db_host, port="5432")
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE users SET max_price = %s, min_size = %s, min_rooms = %s, selected_cities = %s, selected_neighbourhoods = %s WHERE user_id = %s",
        (user_settings["max_price"], user_settings["min_size"], user_settings["min_rooms"], user_settings["selected_cities"], user_settings["selected_neighbourhoods"], user_id)
    )
    connection.commit()
    cursor.close()
    connection.close()

# Main Streamlit app
st.sidebar.header("User Authentication")
user_id = st.sidebar.text_input("User ID")

df = load_data()

filtered_df = df

# Function to check if the user ID exists
def check_user_id(user_id):
    connection = psycopg2.connect(
        database=db_name,
        user=formatted_user,  # Use the correct username format
        password=db_password,
        host=db_host,
        port="5432",
        sslmode='require'
    )
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] > 0

st.header("to open menu click [ > ] on top left")
if user_id:
    logging.debug(f"Checking user ID: {user_id}")
    if check_user_id(int(user_id)):
        logging.debug(f"User ID {user_id} found in database.")
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        
        connection = psycopg2.connect(database=db_name, user=formatted_user, password=db_password, host=db_host, port="5432")
        cursor = connection.cursor()
        cursor.execute("SELECT max_price, min_size, min_rooms, selected_cities, selected_neighbourhoods FROM users WHERE user_id = %s", (user_id,))
        user_settings = cursor.fetchone()

        if user_settings is not None:
            user_settings = {
                "max_price": float(user_settings[0]),
                "min_size": float(user_settings[1]),
                "min_rooms": int(user_settings[2]),
                "selected_cities": user_settings[3] if user_settings[3] else [],
                "selected_neighbourhoods": user_settings[4] if user_settings[4] else []
            }
        else:
            user_settings = {
                "max_price": 0,
                "min_size": 0,
                "min_rooms": 0,
                "selected_cities": [],
                "selected_neighbourhoods": []
            }

        st.sidebar.header("Filter options")

        # Get unique cities and neighborhoods from the dataframe
        selected_cities = user_settings["selected_cities"]
        cities = ['Berlin']

        if not selected_cities:
            selected_cities = cities
        selected_cities = st.sidebar.multiselect('Select Cities', cities, default=cities)

        selected_neighbourhoods = user_settings["selected_neighbourhoods"]
        neighborhoods = [
            'Mitte', 'Moabit', 'Hansaviertel', 'Tiergarten', 'Wedding', 'Gesundbrunnen',
            'Friedrichshain', 'Kreuzberg', 'Prenzlauer Berg', 'Weißensee', 'Blankenburg',
            'Heinersdorf', 'Karow', 'Stadtrandsiedlung Malchow', 'Pankow', 'Blankenfelde',
            'Buch', 'Französisch Buchholz', 'Niederschönhausen', 'Rosenthal', 'Wilhelmsruh',
            'Charlottenburg', 'Wilmersdorf', 'Schmargendorf', 'Grunewald', 'Westend',
            'Charlottenburg-Nord', 'Halensee', 'Spandau', 'Haselhorst', 'Siemensstadt',
            'Staaken', 'Gatow', 'Kladow', 'Hakenfelde', 'Falkenhagener Feld', 'Wilhelmstadt',
            'Steglitz', 'Lichterfelde', 'Lankwitz', 'Zehlendorf', 'Dahlem', 'Nikolassee',
            'Wannsee', 'Schlachtensee', 'Schöneberg', 'Friedenau', 'Tempelhof', 'Mariendorf',
            'Marienfelde', 'Lichtenrade', 'Neukölln', 'Britz', 'Buckow', 'Rudow', 'Gropiusstadt',
            'Alt-Treptow', 'Plänterwald', 'Baumschulenweg', 'Johannisthal', 'Niederschöneweide',
            'Altglienicke', 'Adlershof', 'Bohnsdorf', 'Oberschöneweide', 'Köpenick', 'Friedrichshagen',
            'Rahnsdorf', 'Grünau', 'Müggelheim', 'Schmöckwitz', 'Marzahn', 'Biesdorf', 'Kaulsdorf',
            'Mahlsdorf', 'Hellersdorf', 'Friedrichsfelde', 'Karlshorst', 'Lichtenberg', 'Falkenberg',
            'Malchow', 'Wartenberg', 'Neu-Hohenschönhausen', 'Alt-Hohenschönhausen', 'Fennpfuhl',
            'Rummelsburg', 'Reinickendorf', 'Tegel', 'Konradshöhe', 'Heiligensee', 'Frohnau',
            'Hermsdorf', 'Waidmannslust', 'Lübars', 'Wittenau', 'Märkisches Viertel', 'Borsigwalde'
        ]

        if not selected_neighbourhoods:
            selected_neighbourhoods = neighborhoods

        selected_neighbourhoods = st.sidebar.multiselect('Select Neighborhoods', neighborhoods, default=neighborhoods)

        # Filter the dataframe based on the selected cities and neighborhoods
        df = df[df['city'].isin(selected_cities) & df['neighbourhood'].isin(selected_neighbourhoods)]

        max_price = user_settings["max_price"]
        if pd.isnull(max_price):
            max_price = 0

        min_size = user_settings["min_size"]
        if pd.isnull(min_size):
            min_size = 0

        min_rooms = user_settings["min_rooms"]
        if pd.isnull(min_rooms):
            min_rooms = 0

        if pd.isna(df["price"].min()):
            st.header("No Results. Please adapt your settings.")
            st.write("Anyway, when there will be results according to your settings in future, you will get notified!")
        else:
            max_price = st.sidebar.slider("Max price (Kaltmiete) [ € ]", min_value=int(df["price"].min()), max_value=int(df["price"].max()), value=int(max_price))
            min_size = st.sidebar.slider("Min size [ m² ]", min_value=int(df["size"].min()), max_value=int(df["size"].max()), value=int(min_size))
            min_rooms = st.sidebar.slider("Min rooms [ # ]", min_value=int(df["rooms"].min()), max_value=int(df["rooms"].max()), value=int(min_rooms))

        filtered_df = filter_data(df, max_price, min_size, min_rooms, selected_cities, selected_neighbourhoods)
        map_df = filtered_df[["id", "address", "rooms", "size", "price", "link", "image_url", "latitude", "longitude", "postcode", "datetime", "neighbourhood", "city"]].dropna()

        user_settings = {
            "max_price": max_price,
            "min_size": min_size,
            "min_rooms": min_rooms,
            "selected_cities": selected_cities,
            "selected_neighbourhoods": selected_neighbourhoods,
        }
        st.sidebar.write(f"{len(filtered_df)} results have been found.")    
        store_user_settings(user_id, user_settings)

    else:
        logging.debug(f"User ID {user_id} not found in database.")
        st.header("Please start the bot in Telegram first.")

if st.checkbox("Wanna see the results on a map?"):
    map_df = map_df.dropna()
    if not map_df.empty:
        st.title('Flats on a Map:')
        center = [map_df['latitude'].mean(), map_df['longitude'].mean()]
        m = folium.Map(location=center, zoom_start=10)
        for _, row in map_df.iterrows():
            folium.Marker([row['latitude'], row['longitude']], popup=row['address']).add_to(m)
        folium_static(m)
    else:
        st.header("Nothing to show.")
    if df['postcode'].isnull().values.any() == True:
        st.write("!!! ATTENTION !!!\n\nThere are flats in the list that can't be displayed on the map!\n\n(these are the ones showing 'none' in postcode)")

st.dataframe(filtered_df)

fig = px.histogram(filtered_df, x="price", title="Price Distribution", nbins=100)
st.plotly_chart(fig)

fig = px.histogram(filtered_df, x="size", title="Size Distribution", nbins=50)
st.plotly_chart(fig)

fig = px.histogram(filtered_df, x="rooms", title="Rooms Distribution", nbins=10)
st.plotly_chart(fig)



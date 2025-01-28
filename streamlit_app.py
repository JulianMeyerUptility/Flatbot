import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import psycopg2
from datetime import datetime
import os

def load_data():
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM results")
    df = pd.DataFrame(cursor.fetchall(), columns=["ID", "address", "rooms", "size", "price", "link", "image_url", "latitude", "longitude", "postcode", "datetime", "neighborhood", "city", "district"])
    connection.close()
    return df

def filter_data(df, max_price, min_size, min_rooms, selected_cities, selected_neighborhoods):
    filtered_df = df[
        (df["price"] <= max_price) &
        (df["size"] >= min_size) &
        (df["rooms"] >= min_rooms) &
        df["city"].isin(selected_cities) &
        df["neighborhood"].isin(selected_neighborhoods)
    ]
    return filtered_df

def store_user_settings(user_id, user_settings):
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET max_price = %s, min_size = %s, min_rooms = %s, selected_cities = %s, selected_neighborhoods = %s WHERE user_id = %s",
                   (user_settings["max_price"], user_settings["min_size"], user_settings["min_rooms"], user_settings["selected_cities"], user_settings["selected_neighborhoods"], user_id))
    connection.commit()
    connection.close()

# Main Streamlit app
st.sidebar.header("User Authentication")
user_id = st.sidebar.text_input("User ID")
# print(user_id)

df = load_data()
# print(f"df: {df}")

filtered_df = df
# print(f"filtered_df: {filtered_df}")

map_df = filtered_df[["ID", "address", "rooms", "size", "price", "link", "image_url", "latitude", "longitude", "postcode", "datetime", "neighborhood", "city"]].dropna()
# print(f"map_df: {map_df}")

# Function to check if the user ID exists
def check_user_id(user_id):
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (user_id,))
    count = cursor.fetchone()[0]
    connection.close()
    return count > 0

st.header("to open menu click [ > ] on top left")
if user_id:
    if check_user_id(int(user_id)):

        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        
        connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
        cursor = connection.cursor()
        cursor.execute("SELECT max_price, min_size, min_rooms, max_age, selected_cities, selected_neighborhoods FROM users WHERE user_id = %s", (user_id,))
        user_settings = cursor.fetchone()

        if user_settings is not None:
            user_settings = {
                "max_price": float(user_settings[0]),
                "min_size": float(user_settings[1]),
                "min_rooms": int(user_settings[2]),
                "max_age": user_settings[3],
                "selected_cities": user_settings[4],
                "selected_neighborhoods": user_settings[5]
            }
        else:
            user_settings = {
                "max_price": 0,#round(df["price"].max()),
                "min_size": 0,#round(df["size"].min()),
                "min_rooms": 0,#int(round(df["rooms"].min())),
                "max_age": 0,
                "selected_cities": [],
                "selected_neighborhoods": []
            }

        st.sidebar.header("Filter options")

        # Get unique cities and neighborhoods from the dataframe
        selected_cities = user_settings["selected_cities"]
        cities = ['Berlin']

        if pd.isnull(selected_cities):
            selected_cities = cities
        # print(selected_cities)
        selected_cities = st.sidebar.multiselect('Select Cities', cities, default=cities)

        selected_neighborhoods = user_settings["selected_neighborhoods"]
        neighborhoods = [
    'Mitte',
    'Moabit',
    'Hansaviertel',
    'Tiergarten',
    'Wedding',
    'Gesundbrunnen',
    'Friedrichshain',
    'Kreuzberg',
    'Prenzlauer Berg',
    'Weißensee',
    'Blankenburg',
    'Heinersdorf',
    'Karow',
    'Stadtrandsiedlung Malchow',
    'Pankow',
    'Blankenfelde',
    'Buch',
    'Französisch Buchholz',
    'Niederschönhausen',
    'Rosenthal',
    'Wilhelmsruh',
    'Charlottenburg',
    'Wilmersdorf',
    'Schmargendorf',
    'Grunewald',
    'Westend',
    'Charlottenburg-Nord',
    'Halensee',
    'Spandau',
    'Haselhorst',
    'Siemensstadt',
    'Staaken',
    'Gatow',
    'Kladow',
    'Hakenfelde',
    'Falkenhagener Feld',
    'Wilhelmstadt',
    'Steglitz',
    'Lichterfelde',
    'Lankwitz',
    'Zehlendorf',
    'Dahlem',
    'Nikolassee',
    'Wannsee',
    'Schlachtensee',
    'Schöneberg',
    'Friedenau',
    'Tempelhof',
    'Mariendorf',
    'Marienfelde',
    'Lichtenrade',
    'Neukölln',
    'Britz',
    'Buckow',
    'Rudow',
    'Gropiusstadt',
    'Alt-Treptow',
    'Plänterwald',
    'Baumschulenweg',
    'Johannisthal',
    'Niederschöneweide',
    'Altglienicke',
    'Adlershof',
    'Bohnsdorf',
    'Oberschöneweide',
    'Köpenick',
    'Friedrichshagen',
    'Rahnsdorf',
    'Grünau',
    'Müggelheim',
    'Schmöckwitz',
    'Marzahn',
    'Biesdorf',
    'Kaulsdorf',
    'Mahlsdorf',
    'Hellersdorf',
    'Friedrichsfelde',
    'Karlshorst',
    'Lichtenberg',
    'Falkenberg',
    'Malchow',
    'Wartenberg',
    'Neu-Hohenschönhausen',
    'Alt-Hohenschönhausen',
    'Fennpfuhl',
    'Rummelsburg',
    'Reinickendorf',
    'Tegel',
    'Konradshöhe',
    'Heiligensee',
    'Frohnau',
    'Hermsdorf',
    'Waidmannslust',
    'Lübars',
    'Wittenau',
    'Märkisches Viertel',
    'Borsigwalde'
]


        if pd.isnull(selected_neighborhoods):
            selected_neighborhoods = neighborhoods


        selected_neighborhoods = st.sidebar.multiselect('Select Neighborhoods', neighborhoods, default=neighborhoods)

        # Filter the dataframe based on the selected cities and neighborhoods
        df = df[df['city'].isin(selected_cities) & df['neighborhood'].isin(selected_neighborhoods)]

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

        

        # # Add a slider for max_age in days
        # max_age = user_settings["max_age"]  
        # today = datetime.today().date()

        # valid_dates = df["datetime"].dropna()  # Exclude rows with missing dates
        # if not valid_dates.empty:
        #     min_date = valid_dates.min().date()
        #     max_date = valid_dates.max().date()
        #     age_delta = (today - min_date).days
        #     if age_delta < 0:
        #         age_delta = 0
        # else:
        #     min_date = today
        #     max_date = today
        #     age_delta = 0

        # max_age = st.sidebar.slider("Max announcement age [days]", min_value=0, max_value=age_delta+1, value=max_age)

        filtered_df = filter_data(df, max_price, min_size, min_rooms, selected_cities, selected_neighborhoods)
        # Generate df without NaN for the map
        map_df = filtered_df[["ID", "address", "rooms", "size", "price", "link", "image_url", "latitude", "longitude", "postcode", "datetime", "neighborhood", "city"]].dropna()
        # print(df)
        # Store user settings in the database
        user_settings = {
            "max_price": max_price,
            "min_size": min_size,
            "min_rooms": min_rooms,
            # "max_age": max_age,
            "selected_cities": selected_cities,
            "selected_neighborhoods": selected_neighborhoods,
        }
        st.sidebar.write(f"{len(filtered_df)} results have been found.")    
        # Store user settings in the database
        store_user_settings(user_id, user_settings)

    else:
        st.header("Please start the bot in Telegram first.")

if st.checkbox("Wanna see the results on a map?"):
    map_df = map_df.dropna()
    if not map_df.empty:
        st.title('Flats on a Map:')
        # Set the initial map center coordinates
        center = [map_df['latitude'].mean(), map_df['longitude'].mean()]
        # Create a Folium map
        m = folium.Map(location=center, zoom_start=10)
        # Add markers to the map based on the dataframe
        for _, row in map_df.iterrows():
            folium.Marker([row['latitude'], row['longitude']], popup=row['address']).add_to(m)
        # Display the map in Streamlit
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



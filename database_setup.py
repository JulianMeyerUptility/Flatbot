import os
from sqlalchemy import create_engine, Column, Integer, Numeric, String, TIMESTAMP, MetaData, Table, ARRAY
from sqlalchemy.ext.declarative import declarative_base
import psycopg2

Base = declarative_base()
metadata = MetaData()

# Define table schemas
results = Table('results', metadata,
                Column('id', Integer, primary_key=True),
                Column('address', String(255)),
                Column('rooms', Integer),
                Column('size', Integer),
                Column('price', Numeric),
                Column('link', String(255)),
                Column('image_url', String(255)),
                Column('latitude', Numeric),
                Column('longitude', Numeric),
                Column('postcode', String(10)),
                Column('datetime', TIMESTAMP),
                Column('neighbourhood', String(255)),
                Column('city', String(255)))

sent_results = Table('sent_results', metadata,
                     Column('id', Integer, primary_key=True),
                     Column('user_id', Integer),
                     Column('result_id', Integer),
                     Column('sent', TIMESTAMP(timezone=True)))

users = Table('users', metadata,
              Column('user_id', Integer, primary_key=True),
              Column('max_price', Numeric(10, 2)),
              Column('min_size', Numeric(10, 2)),
              Column('min_rooms', Numeric(10, 2)),
              Column('max_age', Integer),  # Add max_age column
              Column('selected_cities', ARRAY(String)),  # Add selected_cities column
              Column('selected_neighborhoods', ARRAY(String)))  # Add selected_neighborhoods column

# Use environment variables for database connection
db_user = os.getenv('DB_USER', 'flatbot_db')
db_password = os.getenv('DB_PASSWORD', 'DDQ9Gv7IABBqu1WrTMZt')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'flatbotdb')

# Create the PostgreSQL user if it doesn't exist
def create_user():
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',  # Connect as the postgres superuser
        password='postgres',  # Replace with the postgres superuser password
        host=db_host
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{db_user}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_password}'")
        cursor.execute(f"ALTER USER {db_user} CREATEDB")
    cursor.close()
    conn.close()

create_user()

# Create the database if it doesn't exist
def create_database():
    conn = psycopg2.connect(
        dbname='postgres',
        user=db_user,
        password=db_password,
        host=db_host
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f'CREATE DATABASE {db_name}')
    cursor.close()
    conn.close()

create_database()

# Create the database engine
engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}')
metadata.create_all(engine)

print("Tables created successfully.")
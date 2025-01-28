import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    max_price = Column(Numeric(10, 2))
    min_size = Column(Numeric(10, 2))
    min_rooms = Column(Numeric(10, 2))

class Searches(Base):
    __tablename__ = 'searches'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    result_id = Column(Integer)
    sent = Column(Boolean)

class Results(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    result_id = Column(Integer)
    sent = Column(Boolean)

# Use environment variables for database connection
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}')
Base.metadata.create_all(engine)

# Maybe get logging table with timestamps
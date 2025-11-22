import os
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

connector = Connector()

def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME
    )
    return conn


engine = create_engine(
    "mysql+pymysql://",
    creator=getconn,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # erstellt eine Session-Klasse, die für die Interaktion mit der Datenbank verwendet wird
Base = declarative_base()


# Dependency für FastAPI 
def get_db():
    db = SessionLocal() # erstellt eine neue Datenbank-Session
    try:
        yield db # gibt die Datenbank-Session zurück
    finally:
        db.close() # schließt die Datenbank-Session

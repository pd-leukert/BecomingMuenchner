from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .datamodel import Person
from pydantic import BaseModel
from .tools import get_pdf_urls, upload_pdf
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Tabellen erstellen (nur einmal beim Start; in Produktion besser Migrations-Tool nutzen)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    yield

app = FastAPI(
    title="Kunden API",
    description="API zum Verwalten von Kundendaten",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic Schemas
class CustomerCreate(BaseModel):
    vorname: str
    nachname: str
    addresse: str
    ## weitere auch setzen 


class CustomerRead(BaseModel):
    vorname: str
    nachname: str
    addresse: str

    class Config:
        orm_mode = True


@app.get("/")
def root():
    return {"message": "Kunden API läuft"}


# Create
@app.post("/customers", response_model=CustomerRead)
def create_customer(person: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = Person(
        vorname = person.vorname,
        nachname = person.nachname,
    )
    db.add(db_customer)
    try:
        db.commit()
        db.refresh(db_customer)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Kunde konnte nicht angelegt werden (evtl. doppelte Email?)")
    return db_customer



# Read one
@app.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(person_id: int, db: Session = Depends(get_db)):
    customer = db.query(Person).filter(Person.id == person_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return customer


@app.get("/pdfs")
def list_pdfs():
    return get_pdf_urls()


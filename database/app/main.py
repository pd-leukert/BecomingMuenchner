from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .datamodel import Application, Document
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

class Document(BaseModel):
    document_kind: str
    criteria: str
    url: str
    result: bool
    message: str

    class Config:
        orm_mode = True
class Application(BaseModel):
    id: int
    vorname: str
    nachname: str
    geburtsdatum: str
    addresse: str
    staatsangehoerigkeit: str
    Einkommensnachweise: str
    Mietvertrag: str
    Aufenthaltstitel1: str
    Aufenthaltstitel2: str
    Aufenthaltstitel3: str
    Pass: str
    sprachzertifikat: str
    einbürgerungszertifkat: str
    status: str
    result: bool

    class Config:
        orm_mode = True


@app.get("/")
def root():
    return {"message": "Kunden API läuft"}

# response model definiert Format der Antwort
# Create
@app.post("/Applications", response_model=Application)
def create_application(application: Application, db: Session = Depends(get_db)):
    db_application = Application(
        id = application.id,
        vorname = application.vorname,
        nachname = application.nachname,
        adresse = application.addresse,
        geburtsdatum = application.geburtsdatum,
        staatsangehoerigkeit = application.staatsangehoerigkeit,
        Einkommensnachweise = application.Einkommensnachweise,
        Mietvertrag = application.Mietvertrag,
        Aufenthaltstitel1 = application.Aufenthaltstitel1,
        Aufenthaltstitel2 = application.Aufenthaltstitel2,               
        Aufenthaltstitel3 = application.Aufenthaltstitel3,
        Pass = application.Pass,
        sprachzertifikat = application.sprachzertifikat,
        einbürgerungszertifkat = application.einbürgerungszertifkat,
        status = application.status,
        result = application.result
    )
    db.add(db_application)
    try:
        db.commit()
        db.refresh(db_application)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Kunde konnte nicht angelegt werden (evtl. doppelte Email?)")
    return db_application

@app.post("/Documents", response_model=Document)
def create_document(document: Document, db: Session = Depends(get_db)):
    db_document = Document(
        id = document.id,
        document_kind = document.document_kind,
        criteria = document.criteria,
        url = document.url,
        result = document.result,
        message = document.message
    )
    db.add(db_document)
    try:
        db.commit()
        db.refresh(db_document)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Dokument konnte nicht angelegt werden")
    return db_document


# Read one
@app.get("/getApplications/{application_id}", response_model=Application)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return application


@app.post("/update_status_application/{application_id}", response_model=Application)
def update_status_application(application_id: int, status: str, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    application.status = status
    db.commit()
    db.refresh(application)
    return application

@app.post("/update_result_application/{application_id}")
def update_result_application(application_id: int, result: bool, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    application.result = result
    db.commit()
    db.refresh(application)
    return application

@app.post("/update_result_message_document/{application_id}/{document_kind}/{criteria}", response_model=Document)
def update_status_document(application_id: int, document_kind: str, criteria: str, result: bool, message: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == application_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    document.result = result
    document.message = message
    db.commit()
    db.refresh(document)
    return document


class DocumentResult(BaseModel):
    result: bool
    message: str

    class Config:
        orm_mode = True

@app.get("/get_result_message_document/{application_id}/{document_kind}/{criteria}", response_model=DocumentResult)
def get_result_message_document(application_id: int, document_kind: str, criteria: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == application_id, Document.document_kind == document_kind, Document.criteria == criteria).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    return document

@app.get("/get_documents_by_application/{application_id}", response_model=list[Document])
def get_documents_by_application(application_id: int, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.id == application_id).all()
    if not documents:
        raise HTTPException(status_code=404, detail="Dokumente nicht gefunden")
    return documents

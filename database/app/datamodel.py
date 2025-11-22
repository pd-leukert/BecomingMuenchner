from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Application(Base):
    __tablename__ = "Applications"

    id = Column(Integer, primary_key=True, index=True)
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    geburtsdatum = Column(String(10), nullable=True)
    adresse = Column(String(200), nullable=True)
    staatsangehoerigkeit = Column(String(100), nullable=True)
    Einkommensnachweise = Column(String(100), nullable=True)
    Mietvertrag = Column(String(100), nullable=True)
    Aufenthaltstitel1 = Column(String(100), nullable=True)
    Aufenthaltstitel2 = Column(String(100), nullable=True)
    Aufenthaltstitel3 = Column(String(100), nullable=True)
    Pass = Column(String(100), nullable=True)
    sprachzertifikat = Column(String(100), nullable=True) # speicher die URl 
    einbürgerungszertifkat = Column(String(100))
    status = Column(String(100))
    result = Column(Boolean, default=False)


class Document(Base):
    __tablename__ = "Documents"
    id = Column(Integer, primary_key=True, index=True) # von Antrag 
    document_kind = Column(String(100), nullable=False) # z.B. Einkommensnachweis, Mietvertrag
    criteria = Column(String(100), nullable=False) # welche Anforderungen muss das Dokument erfüllen 
    url = Column(String(200), nullable=False) # von google storage 
    result = Column(Boolean) # ob das Dokument den Anforderungen entspricht
    message = Column(String(200)) # wieso scheiterert das Dokument




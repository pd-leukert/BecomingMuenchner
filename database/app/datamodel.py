from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Person(Base):
    __tablename__ = "Personen"

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


class Dokument(Base):
    __tablename__ = "Dokumente"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(200), nullable=False)
    result = Column(Boolean)




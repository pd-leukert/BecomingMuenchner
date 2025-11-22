from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from .database import Base


class Application(Base):
    __tablename__ = "Applications"

    id = Column(Integer, primary_key=True, index=True)
    vorname = Column(String(255), index=True)
    nachname = Column(String(255), index=True)
    geburtsdatum = Column(String(50))
    addresse = Column(String(500))
    staatsangehoerigkeit = Column(String(100))
    
    # WICHTIG: 'Text' statt 'String(2048)' verwenden, um das Row-Size-Limit zu umgehen
    Einkommensnachweise = Column(Text) 
    Mietvertrag = Column(Text)
    Aufenthaltstitel1 = Column(Text)
    Aufenthaltstitel2 = Column(Text)
    Aufenthaltstitel3 = Column(Text)
    Pass = Column(Text)
    sprachzertifikat = Column(Text)
    einbürgerungstest = Column(Text)
    
    status = Column(String(50))
    result = Column(Boolean, default=False)

class Document(Base):
    __tablename__ = "Documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, index=True)
    document_kind = Column(String(255))
    criteria = Column(String(255))
    
    # Auch hier Text verwenden
    url = Column(Text) 
    result = Column(Boolean)
    message = Column(Text)




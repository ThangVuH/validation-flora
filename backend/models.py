from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Boolean, Text

Base = declarative_base()

class Publication(Base):
    __tablename__ = 'openalex_publications'
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True)
    # source = Column(String)
    doi = Column(String)
    title = Column(String)
    type = Column(String)
    source = Column(String)
    year = Column(Integer)
    # Optional validation fields:
    isValid = Column(Boolean, default=False)
    comment = Column(Text, nullable=True)

class FloraPublication(Base):
    __tablename__ = 'flora_publications'
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True)
    doi = Column(String)
    title = Column(String)
    source = Column(String)
    year = Column(Integer)
    # # Optional validation fields:
    # isValid = Column(Boolean, default=False)
    # comment = Column(Text, nullable=True)

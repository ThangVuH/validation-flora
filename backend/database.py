from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config

# Create engine using the URI from the config
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Create a scoped session for thread safety
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
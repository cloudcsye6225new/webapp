from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


import os
    # Load environment variables from the ".env" file
load_dotenv(".env")
POSTGRES_PASSWORD = os.getenv("PGPASSWORD")
POSTGRES_HOST = os.getenv("PGHOST")
POSTGRES_DATABASE=os.getenv("DATABASE_NAME")
        
       

DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"
  

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


import os
    # Load environment variables from the ".env" file
is_github_actions= os.getenv("CI") == "true"

if is_github_actions:

    POSTGRES_PASSWORD = os.getenv("PGPASSWORD")
    POSTGRES_HOST =os.getenv("PGHOST")
    print(POSTGRES_HOST)
    print(POSTGRES_HOST)
    print(POSTGRES_HOST)

    DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/cloud_bd"

else:
    # Load environment variables from the ".env" file
        load_dotenv("app.env")
        POSTGRES_PASSWORD = os.getenv("DB_PASSWORD")
        print(POSTGRES_PASSWORD)
        POSTGRES_HOST = os.getenv("DB_HOST")
        POSTGRES_DATABASE=os.getenv("DB_NAME")
        POSTGRES_USER = os.getenv("DB_USER")

        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"
  

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
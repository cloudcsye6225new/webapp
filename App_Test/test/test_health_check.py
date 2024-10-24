import os
import sys
file_dir = os.path.dirname(os.path.abspath(__file__))
root_folder_dir = os.path.abspath(os.path.join(file_dir, os.pardir, os.pardir))
sys.path.append(root_folder_dir+"/App_Test/")

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import status
from fastapi.security import HTTPBasicCredentials

import base64

from database import Base, get_db
from main import app
from routes.user import get_user

from dotenv import load_dotenv

is_github_actions= os.getenv("CI") == "true"

if is_github_actions:
    POSTGRES_PASSWORD = os.getenv("PGPASSWORD")
    POSTGRES_HOST = os.getenv("PGHOST")
    POSTGRES_DATABASE = os.getenv("TEST_DATABASE")
    DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"
else:
    load_dotenv(".env")
    POSTGRES_PASSWORD = os.getenv("PGPASSWORD")
    print(POSTGRES_PASSWORD)
    POSTGRES_HOST = os.getenv("PGHOST")
    POSTGRES_DATABASE=os.getenv("TEST_DATABASE")
    

    DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"


engine = create_engine(DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind = engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
print(1)
# def override_get_current_user():
#     return {'username': 'john.doe@example.com', 'password': 'password123'}

app.dependency_overrides[get_db] = override_get_db
# app.dependency_overrides[get_user] = override_get_current_user

client = TestClient(app)

# def test_read_all_authenticated():
#     response = client.get("/healthz")
#     assert response.status_code == status.HTTP_200_OK

def test_create_user():
    response = client.post(
        "/v1/user",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "password123"
        }
    )
    if response.status_code == status.HTTP_201_CREATED:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == 400 
    # assert response.json()["email"] == "john.doe@example.com"

# def test_get_user():
#     response = client.get("/users/get_user")
#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["email"] == "john.doe@example.com"

def get_basic_auth_header(username, password):
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode("ascii")).decode("ascii")
    return f"Basic {encoded_credentials}"

def test_get_user():
    auth_header = get_basic_auth_header("john.doe@example.com", "password123")
    response = client.get(
        "/v1/user/self",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "john.doe@example.com"

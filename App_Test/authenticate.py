import base64
from fastapi import Depends, HTTPException, status, utils
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from database import get_db
from Models import models
import bcrypt

security = HTTPBasic()

# Define a dependency function to verify user credentials and retrieve the user from the database
def get_authenticated_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == credentials.username).first()
    if not user:

        raise HTTPException(
            status_code=401,  # Return a 401 Unauthorized status code
            detail="User not found",
        )

    else:
        user = db.query(models.User).filter(
        
            models.User.email == credentials.username,
        
        ).first()
        if bcrypt.checkpw(credentials.password.encode('utf-8'), user.password.encode('utf-8')):

            return user
        


        else  : 

            raise HTTPException(
                status_code=401,  # Return a 401 Unauthorized status code
                detail="Wrong credentials",
            )
    
    
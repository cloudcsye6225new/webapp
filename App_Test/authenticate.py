from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db
from Models import models
import bcrypt

security = HTTPBasic()

def get_authenticated_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):

    # Query user by email (username from HTTPBasic credentials)
    user = db.query(models.User).filter(models.User.email == credentials.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # Return 401 Unauthorized
            detail="User not found",
        )

    # Verify password using bcrypt
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # Return 401 Unauthorized
            detail="Wrong credentials",
        )

      # Check if the user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Complete the email verification process.",
        )

    return user

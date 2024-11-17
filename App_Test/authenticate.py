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

    # Check email verification status
    email_verification = db.query(models.EmailVerification).filter_by(user_id=user.id).first()
    if not email_verification or email_verification.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # Return 403 Forbidden
            detail="Email verification required. Complete the email verification process."
        )

    return user

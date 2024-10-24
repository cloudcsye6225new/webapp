from fastapi import APIRouter, Depends, HTTPException, status, Response
from Models.models import User 
from Models import models
from database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
from Schema import schema
from sqlalchemy.exc import SQLAlchemyError
from authenticate import get_authenticated_user
import bcrypt
from datetime import datetime

userRouter = APIRouter()


models.Base.metadata.create_all(bind = engine)

@userRouter.post('/v1/user', status_code= status.HTTP_201_CREATED, response_model= schema.UserOut)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()
    print(existing_user)
    if existing_user:
            raise HTTPException(status_code= 400, detail="Email already registered.")

    try:
        new_user = models.User(**user.dict())
        password_hash = bcrypt.hashpw(new_user.password.encode('utf-8'), bcrypt.gensalt())
        user_model = models.User(
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            email=new_user.email,
            password=password_hash.decode('utf-8'),
        )
        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        


        return user_model
    except Exception as e:
        # Handle exceptions, possibly raise an HTTPException if there's an error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User creation failed")
    finally:
        # Close the database session when done, regardless of success or failure
        db.close()

@userRouter.put("/v1/user/self")
def update_user(
    user_update: schema.UserUpdate,
    current_user: models.User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    if not any([user_update.first_name, user_update.last_name, user_update.password]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    try:
        if user_update.first_name:
            current_user.first_name = user_update.first_name
        if user_update.last_name:
            current_user.last_name = user_update.last_name
        if user_update.password:
            hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
            current_user.password = hashed_password.decode('utf-8')
        if user_update.email!=current_user.email :
            raise ValueError("Email cannot be updated")
        current_user.account_updated = datetime.utcnow()
        db.commit()
        db.refresh(current_user)

        return Response(status_code= 204)
    except ValueError as v:
        raise HTTPException(status_code= 400, detail = f"{v}")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred {e} while updating user information"
        )
    
@userRouter.get('/v1/user/self', response_model=schema.UserOut)
def get_user(current_user: User = Depends(get_authenticated_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return current_user

# user.py

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from Models.models import User
from Models import models
from database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
from Schema import schema
from sqlalchemy.exc import SQLAlchemyError
from authenticate import get_authenticated_user
import bcrypt
from datetime import datetime
import logging
import time
from statsd import StatsClient
import os

from PIL import Image
import boto3

from io import BytesIO


from Models.models import User, ImageMetadata

# Set up S3 client using instance IAM role
s3_client = boto3.client("s3")

# Define S3 bucket name (environment variable should be set by user_data or .env file)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


# Define the log directory and file path
log_directory = os.path.join(os.getcwd(), "logs")
log_file_path = os.path.join(log_directory, "app.log")

# Create the log directory if it doesn't exist
os.makedirs(log_directory, exist_ok=True)
# Set up logging
logging.basicConfig(
    filename="./logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set up StatsD client
statsd = StatsClient(host='localhost', port=8125)

userRouter = APIRouter()
models.Base.metadata.create_all(bind=engine)

@userRouter.post('/v1/user', status_code=status.HTTP_201_CREATED, response_model=schema.UserOut)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):
    statsd.incr("api_calls.create_user.count")  # Increment API call count
    start_time = time.time()  # Start timing

    logger.info("Attempting to create a new user with email: %s", user.email)
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        logger.warning("User creation failed - Email already registered: %s", user.email)
        statsd.timing("api_calls.create_user.duration", (time.time() - start_time) * 1000)
        raise HTTPException(status_code=400, detail="Email already registered.")

    try:
        password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        user_model = models.User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password=password_hash.decode('utf-8'),
        )
        
        # Timing database query
        db_start_time = time.time()
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
        statsd.timing("database.create_user_query.duration", (time.time() - db_start_time) * 1000)

        logger.info("User created successfully with email: %s", user.email)
        return user_model
    except Exception as e:
        logger.error("User creation failed due to an exception: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User creation failed")
    finally:
        db.close()
        statsd.timing("api_calls.create_user.duration", (time.time() - start_time) * 1000)  # Record API duration

@userRouter.put("/v1/user/self")
def update_user(
    user_update: schema.UserUpdate,
    current_user: models.User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    statsd.incr("api_calls.update_user.count")
    start_time = time.time()

    logger.info("Attempting to update user with ID: %s", current_user.id)

    if not any([user_update.first_name, user_update.last_name, user_update.password]):
        logger.warning("User update failed - No valid fields to update for user ID: %s", current_user.id)
        statsd.timing("api_calls.update_user.duration", (time.time() - start_time) * 1000)
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
        if user_update.email != current_user.email:
            logger.warning("User update failed - Email cannot be updated for user ID: %s", current_user.id)
            raise ValueError("Email cannot be updated")
        current_user.account_updated = datetime.utcnow()
        
        db_start_time = time.time()
        db.commit()
        db.refresh(current_user)
        statsd.timing("database.update_user_query.duration", (time.time() - db_start_time) * 1000)

        logger.info("User updated successfully for user ID: %s", current_user.id)
        return Response(status_code=204)
    except ValueError as v:
        logger.error("User update failed with validation error: %s", v)
        raise HTTPException(status_code=400, detail=str(v))
    except Exception as e:
        db.rollback()
        logger.error("User update failed due to an exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred {e} while updating user information"
        )
    finally:
        db.close()
        statsd.timing("api_calls.update_user.duration", (time.time() - start_time) * 1000)

@userRouter.get('/v1/user/self', response_model=schema.UserOut)
def get_user(current_user: User = Depends(get_authenticated_user)):
    statsd.incr("api_calls.get_user.count")
    start_time = time.time()

    if not current_user:
        logger.warning("User retrieval failed - User not found")
        statsd.timing("api_calls.get_user.duration", (time.time() - start_time) * 1000)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    logger.info("Retrieved user details for user ID: %s", current_user.id)
    statsd.timing("api_calls.get_user.duration", (time.time() - start_time) * 1000)
    return current_user


from uuid import uuid4


@userRouter.post("/v1/user/self/pic")
async def upload_profile_picture(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    """
    Endpoint to upload a profile picture for the current user.
    Expects a binary image file in the request body.
    """
    # Read binary data from the request body
    image_data = await request.body()

    # Open and validate the uploaded image
    try:
        image = Image.open(BytesIO(image_data))
        image.verify()
    except Exception as e:
        logger.warning("Uploaded file is not a valid image by user: %s", current_user.id)
        raise HTTPException(status_code=400, detail="Invalid image file.")

    # Generate a unique S3 key for the image
    s3_key = f"profile_pictures/{current_user.id}/{uuid4()}.png"
    upload_date = datetime.utcnow().strftime("%Y-%m-%d")

    # Upload the image to S3
    try:
        s3_client.upload_fileobj(
            BytesIO(image_data),
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": "image/png"}
        )
        logger.info("Uploaded profile picture for user: %s", current_user.id)
    except Exception as e:
        logger.error("Error uploading file to S3: %s", e)
        raise HTTPException(status_code=500, detail=f"Error uploading file to S3. Internal error: {str(e)}")

    # Save image metadata to the database
    image_metadata = ImageMetadata(
        id=uuid4(),
        user_id=current_user.id,
        file_name="profile_picture.png",
        url=f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}",
        upload_date=upload_date,
    )
    db.add(image_metadata)
    db.commit()

    # Prepare and return the response with image metadata
    response = {
        "file_name": "profile_picture.png",
        "id": str(image_metadata.id),
        "url": image_metadata.url,
        "upload_date": upload_date,
        "user_id": str(current_user.id)
    }
    return response

@userRouter.get("/v1/user/self/pic")
async def get_profile_picture(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to get the profile picture URL for the current user.
    """
    statsd.incr("api_calls.get_profile_picture.count")
    start_time = time.time()

    try:
        image_metadata = db.query(ImageMetadata).filter_by(user_id=current_user.id).first()
        if not image_metadata:
            logger.warning("No profile picture found for user: %s", current_user.id)
            raise HTTPException(status_code=404, detail="Profile picture not found.")

        logger.info("Retrieved profile picture URL for user: %s", current_user.id)
        statsd.timing("api_calls.get_profile_picture.duration", (time.time() - start_time) * 1000)
        return {"filename": image_metadata.file_name, "id":image_metadata.id, "url": image_metadata.url, "upload_date": image_metadata.upload_date, "user_id": image_metadata.user_id}
    except Exception as e:
        logger.error("Error retrieving profile picture for user %s: %s", current_user.id, e)
        raise HTTPException(status_code=500, detail="Error retrieving profile picture.")


@userRouter.delete("/v1/user/self/pic", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_picture(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to delete the profile picture for the current user.
    """
    statsd.incr("api_calls.delete_profile_picture.count")
    start_time = time.time()

    try:
        image_metadata = db.query(ImageMetadata).filter_by(user_id=current_user.id).first()
        if not image_metadata:
            logger.warning("No profile picture found to delete for user: %s", current_user.id)
            raise HTTPException(status_code=404, detail="Profile picture not found.")

        # Delete the image from S3
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=image_metadata.url.split(f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/")[-1])
        db.delete(image_metadata)
        db.commit()

        logger.info("Deleted profile picture for user: %s", current_user.id)
        statsd.timing("api_calls.delete_profile_picture.duration", (time.time() - start_time) * 1000)
        return Response(status_code=204)
    except Exception as e:
        logger.error("Error deleting profile picture for user %s: %s", current_user.id, e)
        raise HTTPException(status_code=404, detail=f"Error deleting profile picture. {e}")


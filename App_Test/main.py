from fastapi import FastAPI
from routes.healthcheck import router as healthcheck_router
from routes.user import userRouter as user_router
# Create the FastAPI app
app = FastAPI()

app.include_router(user_router)

app.include_router(healthcheck_router)

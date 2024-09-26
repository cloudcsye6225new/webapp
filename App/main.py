from fastapi import FastAPI
from routes.healthcheck import router as healthcheck_router
# Create the FastAPI app
app = FastAPI()

app.include_router(healthcheck_router)
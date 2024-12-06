# healthcheck.py

from fastapi import APIRouter, HTTPException, Response, Request
from database import DATABASE_URL
from sqlalchemy import create_engine
import logging
import os
import time
from statsd import StatsClient

# Define the log directory and file path
log_directory = os.path.join(os.getcwd(), "logs")
log_file_path = os.path.join(log_directory, "app.log")

# Create the log directory if it doesn't exist
os.makedirs(log_directory, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set up StatsD client
statsd = StatsClient(host='localhost', port=8125)

router = APIRouter(tags=['health_check'])

def request_has_body(request):
    content_length = request.headers.get("content-length")
    return content_length is not None and int(content_length) > 0

# To connect and query to check if the database is connected
def postgres_status():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect():
            logger.info("Database connection successful")
            return "PostgreSQL server is running"
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return "Not"

@router.get("/healthz")
def root(request: Request):
    statsd.incr("api_calls.health_check.count")
    start_time = time.time()

    logger.info("Health check endpoint called")

    if request.query_params:
        logger.warning("Health check failed - Unexpected query parameters")
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(status_code=400)
    if request_has_body(request):
        logger.warning("Health check failed - Unexpected request body")
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(status_code=400)
    
    status = postgres_status()
    if "running" in status.lower():
        logger.info("Health check passed - Database is connected")
        headers = {"Cache-Control": "no-cache"}
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(headers=headers)
    else:
        logger.warning("Health check failed - Database is not reachable")
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(status_code=503)

@router.get("/cicd")
def root(request: Request):
    statsd.incr("api_calls.health_check.count")
    start_time = time.time()

    logger.info("Health check endpoint called")

    if request.query_params:
        logger.warning("Health check failed - Unexpected query parameters")
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(status_code=400)
    if request_has_body(request):
        logger.warning("Health check failed - Unexpected request body")
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(status_code=400)
    
    status = postgres_status()
    if "running" in status.lower():
        logger.info("Health check passed - Database is connected")
        headers = {"Cache-Control": "no-cache"}
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(headers=headers)
    else:
        logger.warning("Health check failed - Database is not reachable")
        statsd.timing("api_calls.health_check.duration", (time.time() - start_time) * 1000)
        return Response(status_code=503)


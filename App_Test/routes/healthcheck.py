from fastapi import APIRouter, HTTPException, Response,Request
from database import DATABASE_URL
from sqlalchemy import create_engine

router = APIRouter(    
    tags=['health_check']
)

def request_has_body(request):
    content_length = request.headers.get("content-length")
    return content_length is not None and int(content_length) > 0
#to connect the and query to check if database is connected 
def postgres_status():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect():
            
            # raise HTTPException(status_code=200, detail="PostgreSQL server is running")
            return "PostgreSQL server is running"
    except :
    
        return "Not"

@router.get("/healthz")
def root(request: Request):
       

    if request.query_params:
        return Response(status_code=400)
    if request_has_body(request):
        return Response(status_code=400)
    status = postgres_status()
    if "running" in status.lower():
        headers = {"Cache-Control": "no-cache"}  
        return Response(headers=headers)
        
    else:
        return Response(status_code=503)

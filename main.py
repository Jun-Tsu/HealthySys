import logging
from fastapi import FastAPI
from db import connect_db, disconnect_db, init_db, check_db_status

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Health Information System")

@app.on_event("startup")
async def startup_event():
    init_db()  # Initialize schema
    await connect_db()  # Connect to database

@app.on_event("shutdown")
async def shutdown_event():
    await disconnect_db()  # Disconnect from database

@app.get("/")
async def root():
    logging.info("Root endpoint accessed")
    return {"message": "Health System API is running"}

@app.get("/db-status")
async def db_status():
    logging.info("Database status endpoint accessed")
    return await check_db_status()
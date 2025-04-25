import logging
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Health Information System")

@app.get("/")
async def root():
    logging.info("Root endpoint accessed")
    return {"message": "Health System API is running"}
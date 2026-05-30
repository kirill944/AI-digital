import os
import logging
import time
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from src.model_loader import loader

load_dotenv('configs/.env')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
PORT = int(os.getenv('PORT', 8000))

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger("churn_service")

request_counter = 0
error_counter = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    try:
        loader.load()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    yield
    logger.info("Shutting down...")

app = FastAPI(title="Churn Prediction API", lifespan=lifespan)

class ChurnRequest(BaseModel):
    gender: str
    SeniorCitizen: int = Field(..., ge=0, le=1)
    Partner: str
    Dependents: str
    tenure: int = Field(..., ge=0)
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float = Field(..., ge=0)
    TotalCharges: float = Field(..., ge=0)

    # Валидаторы - Pydantic V2 стиль
    @field_validator('gender', 'Partner', 'Dependents', 'PhoneService', 'MultipleLines',
                     'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                     'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
                     'PaperlessBilling', 'PaymentMethod')
    @classmethod
    def check_not_empty(cls, v):
        if v is None or v == '':
            raise ValueError('Field cannot be empty')
        return v

class PredictionResponse(BaseModel):
    churn_probability: float
    risk_category: str

def get_risk_category(prob: float) -> str:
    if prob < 0.2:
        return "low"
    elif prob < 0.7:
        return "medium"
    else:
        return "high"

@app.get("/health")
async def health():
    if loader.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok"}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: ChurnRequest, http_request: Request):
    global request_counter, error_counter
    request_counter += 1
    start_time = time.time()
    try:
        input_dict = request.dict()
        df = pd.DataFrame([input_dict])
        proba = loader.predict(df)[0]
        duration = time.time() - start_time
        logger.info(f"Prediction done in {duration:.3f}s, prob={proba:.4f}, client={http_request.client.host}")
        return PredictionResponse(churn_probability=proba, risk_category=get_risk_category(proba))
    except Exception as e:
        error_counter += 1
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    return {
        "total_requests": request_counter,
        "total_errors": error_counter,
        "error_rate": error_counter / request_counter if request_counter > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
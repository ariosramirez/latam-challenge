from pydantic import BaseModel, Field, validator, ValidationError
from pydantic.errors import ConfigError
from typing import List, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import joblib
import pandas as pd
import logging
from challenge.model import DelayModel, ROOT_DIR


# Initialize the FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the model and preprocessor globally
delay_model = DelayModel()
preprocessor = None

# Valid values for MES, TIPOVUELO, and OPERA
VALID_MES_VALUES = list(range(1, 13))
VALID_TIPOVUELO_VALUES = ["N", "I"]
VALID_OPERA_VALUES = [
    "American Airlines",
    "Air Canada",
    "Air France",
    "Aeromexico",
    "Aerolineas Argentinas",
    "Austral",
    "Avianca",
    "Alitalia",
    "British Airways",
    "Copa Air",
    "Delta Air",
    "Gol Trans",
    "Iberia",
    "K.L.M.",
    "Qantas Airways",
    "United Airlines",
    "Grupo LATAM",
    "Sky Airline",
    "Latin American Wings",
    "Plus Ultra Lineas Aereas",
    "JetSmart SPA",
    "Oceanair Linhas Aereas",
    "Lacsa",
]


class FlightData(BaseModel):
    OPERA: str = Field(..., example="Aerolineas Argentinas")
    TIPOVUELO: str = Field(..., example="N")  # National or International
    MES: int = Field(..., example=3)  # Month as an integer

    @validator("MES")
    def validate_mes(cls, v):
        if v not in VALID_MES_VALUES:
            raise HTTPException(status_code=400,
                                detail=f"MES must be within {VALID_MES_VALUES}")
        return v

    @validator("TIPOVUELO")
    def validate_tipovuelo(cls, v):
        if v not in VALID_TIPOVUELO_VALUES:
            raise HTTPException(
                status_code=400,
                detail=f"TIPOVUELO must be one of {VALID_TIPOVUELO_VALUES}")
        return v

    @validator("OPERA")
    def validate_opera(cls, v):
        if v not in VALID_OPERA_VALUES:
            raise HTTPException(
                status_code=400,
                detail=f"OPERA must be one of {VALID_OPERA_VALUES}")
        return v

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


class PredictionRequest(BaseModel):
    flights: List[FlightData]


@app.on_event("startup")
async def load_model():
    global delay_model, preprocessor
    try:
        data = pd.read_csv(
            filepath_or_buffer=f"{ROOT_DIR}/data/data.csv",
            usecols=["OPERA", "TIPOVUELO", "MES", "Fecha-O", "Fecha-I"],
        )

        features, target = delay_model.preprocess(data, target_column="delay")
        delay_model.fit(features=features, target=target)
        logger.info("Model and preprocessor train successfully.")
    except Exception as e:
        logger.error(f"Failed to load model or preprocessor: {e}")
        raise RuntimeError("Failed to load model or preprocessor.")


@app.post("/predict", status_code=200)
async def post_predict(request: PredictionRequest) -> Dict[str, List[int]]:
    try:
        # Convert incoming data to a DataFrame
        df = pd.DataFrame([flight.dict() for flight in request.flights])

        # Preprocess the incoming data
        processed_features = delay_model.preprocess(df, train=False)

        # Make predictions using the  model
        predictions = delay_model.predict(processed_features)

        # Return the predictions as a list in a dictionary
        return {"predict": predictions}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500,
                            detail="An error occurred during prediction.")


@app.get("/health", status_code=200)
async def get_health() -> dict:
    return {"status": "OK"}

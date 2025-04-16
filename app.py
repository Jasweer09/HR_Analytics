from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
from typing import Dict, List, Union
import logging
import json
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

prediction_logger = logging.getLogger("predictions")
prediction_handler = logging.FileHandler("predictions.log")
prediction_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
prediction_logger.addHandler(prediction_handler)
prediction_logger.setLevel(logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="HR Analytics API (Attrition)",
    description="API for predicting employee attrition risk",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the attrition model
try:
    logger.info("Loading attrition model...")
    attrition_model = joblib.load("attrition_model.pkl")
    logger.info(f"Attrition model loaded. Expects {attrition_model.n_features_in_} features.")
except Exception as e:
    logger.error(f"Error loading attrition model: {str(e)}")
    raise Exception(f"Error loading attrition model: {str(e)}")

# Define input data model
class EmployeeData(BaseModel):
    Age: Union[float, int]
    Gender: str
    Department: str
    JobRole: str
    MonthlyIncome: Union[float, int]
    YearsAtCompany: Union[float, int]
    OverTime: str
    JobSatisfaction: Union[float, int]
    WorkLifeBalance: Union[float, int]
    TotalWorkingYears: Union[float, int]
    TrainingTimesLastYear: Union[float, int]
    JobInvolvement: Union[float, int]
    EnvironmentSatisfaction: Union[float, int]
    RelationshipSatisfaction: Union[float, int]

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the HR Analytics API (Attrition). Use /predict_attrition to get predictions."}

# Preprocessing function
def preprocess_data(data: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
    """Preprocess categorical columns into numeric format."""
    data = data.copy()
    if "OverTime" in data.columns:
        data["OverTime"] = data["OverTime"].map({"Yes": 1, "No": 0})
    return data

def preprocess_and_predict(data: pd.DataFrame, model, features: List[str]) -> tuple:
    """Preprocess data and predict using the model."""
    try:
        X = data.reindex(columns=features, fill_value=0)
        predictions = model.predict(X)
        probabilities = model.predict_proba(X) if hasattr(model, "predict_proba") else None
        return predictions, probabilities
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# Single attrition prediction endpoint
@app.post("/predict_attrition")
async def predict_attrition(employee: EmployeeData) -> Dict[str, float]:
    try:
        logger.info("Received request for attrition prediction.")
        logger.info(f"Input data: {employee.model_dump()}")

        # Input validation
        if employee.JobSatisfaction < 1 or employee.JobSatisfaction > 5:
            raise HTTPException(status_code=400, detail="JobSatisfaction must be between 1 and 5.")
        if employee.WorkLifeBalance < 1 or employee.WorkLifeBalance > 5:
            raise HTTPException(status_code=400, detail="WorkLifeBalance must be between 1 and 5.")
        if employee.JobInvolvement < 1 or employee.JobInvolvement > 5:
            raise HTTPException(status_code=400, detail="JobInvolvement must be between 1 and 5.")
        if employee.EnvironmentSatisfaction < 1 or employee.EnvironmentSatisfaction > 5:
            raise HTTPException(status_code=400, detail="EnvironmentSatisfaction must be between 1 and 5.")
        if employee.RelationshipSatisfaction < 1 or employee.RelationshipSatisfaction > 5:
            raise HTTPException(status_code=400, detail="RelationshipSatisfaction must be between 1 and 5.")
        if employee.OverTime not in ["Yes", "No"]:
            raise HTTPException(status_code=400, detail="OverTime must be 'Yes' or 'No'.")
        if employee.Age < 18 or employee.Age > 100:
            raise HTTPException(status_code=400, detail="Age must be between 18 and 100.")
        if employee.MonthlyIncome <= 0:
            raise HTTPException(status_code=400, detail="MonthlyIncome must be greater than 0.")
        if employee.YearsAtCompany < 0:
            raise HTTPException(status_code=400, detail="YearsAtCompany cannot be negative.")
        if employee.TotalWorkingYears < 0:
            raise HTTPException(status_code=400, detail="TotalWorkingYears cannot be negative.")
        if employee.TrainingTimesLastYear < 0:
            raise HTTPException(status_code=400, detail="TrainingTimesLastYear cannot be negative.")
        if employee.Gender not in ["Male", "Female"]:
            raise HTTPException(status_code=400, detail="Gender must be 'Male' or 'Female'.")

        # Convert to DataFrame and preprocess
        data = pd.DataFrame([employee.model_dump()])
        categorical_columns = ["OverTime"]
        data = preprocess_data(data, categorical_columns)

        # Select features
        attrition_features = ["JobSatisfaction", "WorkLifeBalance", "OverTime"]
        prediction, probs = preprocess_and_predict(data, attrition_model, attrition_features)
        probability = float(probs[0][1]) if probs is not None else 0.0

        # Log prediction
        prediction_log = {
            "endpoint": "predict_attrition",
            "input": employee.model_dump(),
            "prediction": {"AttritionRisk": float(prediction[0]), "AttritionRiskProbability": probability}
        }
        prediction_logger.info(json.dumps(prediction_log))

        return {
            "AttritionRisk": float(prediction[0]),
            "AttritionRiskProbability": probability
        }
    except Exception as e:
        logger.error(f"Error predicting attrition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting attrition: {str(e)}")

# Bulk attrition prediction endpoint
@app.post("/predict_attrition_bulk")
async def predict_attrition_bulk(file: UploadFile = File(...)) -> Dict[str, List]:
    try:
        logger.info("Received request for bulk attrition prediction.")
        
        contents = await file.read()
        data = pd.read_csv(io.BytesIO(contents))
        logger.info(f"CSV data loaded with {len(data)} rows.")

        required_columns = [
            "Age", "Gender", "Department", "JobRole", "MonthlyIncome", "YearsAtCompany",
            "OverTime", "JobSatisfaction", "WorkLifeBalance", "TotalWorkingYears",
            "TrainingTimesLastYear", "JobInvolvement", "EnvironmentSatisfaction",
            "RelationshipSatisfaction"
        ]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_columns}")

        # Input validation
        validation_errors = []
        for idx, row in data.iterrows():
            if not pd.isna(row["JobSatisfaction"]) and (row["JobSatisfaction"] < 1 or row["JobSatisfaction"] > 5):
                validation_errors.append(f"Row {idx}: JobSatisfaction must be between 1 and 5.")
            if not pd.isna(row["WorkLifeBalance"]) and (row["WorkLifeBalance"] < 1 or row["WorkLifeBalance"] > 5):
                validation_errors.append(f"Row {idx}: WorkLifeBalance must be between 1 and 5.")
            if not pd.isna(row["JobInvolvement"]) and (row["JobInvolvement"] < 1 or row["JobInvolvement"] > 5):
                validation_errors.append(f"Row {idx}: JobInvolvement must be between 1 and 5.")
            if not pd.isna(row["EnvironmentSatisfaction"]) and (row["EnvironmentSatisfaction"] < 1 or row["EnvironmentSatisfaction"] > 5):
                validation_errors.append(f"Row {idx}: EnvironmentSatisfaction must be between 1 and 5.")
            if not pd.isna(row["RelationshipSatisfaction"]) and (row["RelationshipSatisfaction"] < 1 or row["RelationshipSatisfaction"] > 5):
                validation_errors.append(f"Row {idx}: RelationshipSatisfaction must be between 1 and 5.")
            if row["OverTime"] not in ["Yes", "No"]:
                validation_errors.append(f"Row {idx}: OverTime must be 'Yes' or 'No'.")
            if not pd.isna(row["Age"]) and (row["Age"] < 18 or row["Age"] > 100):
                validation_errors.append(f"Row {idx}: Age must be between 18 and 100.")
            if not pd.isna(row["MonthlyIncome"]) and row["MonthlyIncome"] <= 0:
                validation_errors.append(f"Row {idx}: MonthlyIncome must be greater than 0.")
            if not pd.isna(row["YearsAtCompany"]) and row["YearsAtCompany"] < 0:
                validation_errors.append(f"Row {idx}: YearsAtCompany cannot be negative.")
            if not pd.isna(row["TotalWorkingYears"]) and row["TotalWorkingYears"] < 0:
                validation_errors.append(f"Row {idx}: TotalWorkingYears cannot be negative.")
            if not pd.isna(row["TrainingTimesLastYear"]) and row["TrainingTimesLastYear"] < 0:
                validation_errors.append(f"Row {idx}: TrainingTimesLastYear cannot be negative.")
            if row["Gender"] not in ["Male", "Female"]:
                validation_errors.append(f"Row {idx}: Gender must be 'Male' or 'Female'.")
        if validation_errors:
            raise HTTPException(status_code=400, detail=validation_errors[:10])

        # Preprocess
        categorical_columns = ["OverTime"]
        data = preprocess_data(data, categorical_columns)

        # Predict
        attrition_features = ["JobSatisfaction", "WorkLifeBalance", "OverTime"]
        predictions, probs = preprocess_and_predict(data, attrition_model, attrition_features)

        # Prepare response
        results = [
            {
                "EmployeeIndex": int(idx),
                "AttritionRisk": float(pred),
                "AttritionRiskProbability": float(prob[1]) if probs is not None else 0.0
            }
            for idx, (pred, prob) in enumerate(zip(predictions, probs if probs is not None else [None] * len(predictions)))
        ]

        for result, row in zip(results, data.to_dict("records")):
            prediction_log = {
                "endpoint": "predict_attrition_bulk",
                "input": row,
                "prediction": result
            }
            prediction_logger.info(json.dumps(prediction_log))

        return {"predictions": results}
    except ValueError as ve:
        logger.error(f"ValueError in bulk attrition prediction: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(ve)}")
    except Exception as e:
        logger.error(f"Error predicting bulk attrition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting bulk attrition: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

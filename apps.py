from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Dict, List, Union
import logging
import json
import io
import joblib
import numpy as np
from sklearn.pipeline import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

prediction_logger = logging.getLogger("predictions")
prediction_handler = logging.FileHandler("predictions.log")
prediction_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
prediction_logger.addHandler(prediction_handler)
prediction_logger.setLevel(logging.INFO)

app = FastAPI(
    title="HR Analytics API (Performance & Retention)",
    description="API for predicting employee performance and retention risk",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PERFORMANCE_MODEL_PATH = "performance_model.pkl"
RETENTION_MODEL_PATH = "retention_model.pkl"

try:
    logger.info("Loading performance model...")
    performance_model = joblib.load(PERFORMANCE_MODEL_PATH)
    logger.info(f"Performance model loaded. Expects {performance_model.n_features_in_} features.")
    if hasattr(performance_model, "feature_names_in_"):
        logger.info(f"Performance model expected features: {list(performance_model.feature_names_in_)}")
    if isinstance(performance_model, Pipeline):
        logger.info(f"Pipeline steps: {performance_model.steps}")
except Exception as e:
    logger.error(f"Error loading performance model: {str(e)}")
    raise Exception(f"Error loading performance model: {str(e)}")

try:
    logger.info("Loading retention model...")
    retention_model = joblib.load(RETENTION_MODEL_PATH)
    logger.info(f"Retention model loaded. Expects {retention_model.n_features_in_} features.")
    if hasattr(retention_model, "feature_names_in_"):
        logger.info(f"Retention model expected features: {list(retention_model.feature_names_in_)}")
except Exception as e:
    logger.error(f"Error loading retention model: {str(e)}")
    raise Exception(f"Error loading retention model: {str(e)}")

class EmployeeDataPerformance(BaseModel):
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

class EmployeeDataRetention(BaseModel):
    JobSatisfaction: Union[float, int]
    WorkLifeBalance: Union[float, int]
    JobInvolvement: Union[float, int]
    OverTime: str
    Gender: str
    PerformanceRating: Union[float, int]

@app.get("/")
async def root():
    return {"message": "Welcome to the HR Analytics API (Performance & Retention)."}

def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Raw input passed to model: {data.to_dict(orient='records')}")
    return data

def preprocess_and_predict(data: pd.DataFrame, model, expected_features: List[str]) -> tuple:
    try:
        X = data.reindex(columns=expected_features)
        logger.info(f"Data for prediction: {X.to_dict(orient='records')}")
        predictions = model.predict(X)
        probabilities = model.predict_proba(X) if hasattr(model, "predict_proba") else None
        return predictions, probabilities
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        if isinstance(model, Pipeline):
            final_estimator = model.steps[-1][1]
            logger.info(f"Falling back to final estimator: {final_estimator}")
            X_array = X.values.astype(np.float64)
            predictions = final_estimator.predict(X_array)
            probabilities = final_estimator.predict_proba(X_array) if hasattr(final_estimator, "predict_proba") else None
            return predictions, probabilities
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
@app.post("/predict_performance")
async def predict_performance(employee: EmployeeDataPerformance) -> Dict[str, float]:
    try:
        logger.info("Received request for performance prediction.")
        logger.info(f"Input data: {employee.model_dump()}")

        for field in ["JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "EnvironmentSatisfaction", "RelationshipSatisfaction"]:
            value = getattr(employee, field)
            if value < 1 or value > 5:
                raise HTTPException(status_code=400, detail=f"{field} must be between 1 and 5.")
        for field in ["Age", "YearsAtCompany", "TotalWorkingYears", "TrainingTimesLastYear"]:
            value = getattr(employee, field)
            if value < 0:
                raise HTTPException(status_code=400, detail=f"{field} cannot be negative.")
        if employee.MonthlyIncome <= 0:
            raise HTTPException(status_code=400, detail="MonthlyIncome must be greater than 0.")

        data = pd.DataFrame([employee.model_dump()])
        data = preprocess_data(data)
        features = list(performance_model.feature_names_in_)
        rating, _ = preprocess_and_predict(data, performance_model, features)
        rating = float(rating[0] + 1)

        prediction_logger.info(json.dumps({
            "endpoint": "predict_performance",
            "input": employee.model_dump(),
            "prediction": {"PerformanceRating": rating}
        }))

        return {"PerformanceRating": rating}
    except Exception as e:
        logger.error(f"Error predicting performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting performance: {str(e)}")

@app.post("/predict_retention")
async def predict_retention(employee: dict) -> Dict[str, float]:
    try:
        logger.info("Received request for retention prediction.")
        validated_data = {k: employee[k] for k in ["JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "OverTime", "Gender"]}
        performance_response = await predict_performance(EmployeeDataPerformance(**employee))
        validated_data["PerformanceRating"] = performance_response["PerformanceRating"]
        employee_data = EmployeeDataRetention(**validated_data)

        for field in ["JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "PerformanceRating"]:
            value = getattr(employee_data, field)
            if value < 1 or value > 5:
                raise HTTPException(status_code=400, detail=f"{field} must be between 1 and 5.")

        data = pd.DataFrame([employee_data.model_dump()])
        data = preprocess_data(data)
        features = list(retention_model.feature_names_in_)
        risk, probs = preprocess_and_predict(data, retention_model, features)
        probability = float(probs[0][int(risk[0])]) if probs is not None else 0.0

        prediction_logger.info(json.dumps({
            "endpoint": "predict_retention",
            "input": employee_data.model_dump(),
            "prediction": {"RetentionRisk": float(risk[0]), "RetentionRiskProbability": probability}
        }))

        return {
            "RetentionRisk": float(risk[0]),
            "RetentionRiskProbability": probability
        }
    except Exception as e:
        logger.error(f"Error predicting retention: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting retention: {str(e)}")

@app.post("/predict_performance_bulk")
async def predict_performance_bulk(file: UploadFile = File(...)) -> Dict[str, List]:
    try:
        logger.info("Received request for bulk performance prediction.")
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

        validation_errors = []
        for idx, row in data.iterrows():
            for field in ["JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "EnvironmentSatisfaction", "RelationshipSatisfaction"]:
                if not pd.isna(row[field]) and (row[field] < 1 or row[field] > 5):
                    validation_errors.append(f"Row {idx}: {field} must be between 1 and 5.")
            if not pd.isna(row["MonthlyIncome"]) and row["MonthlyIncome"] <= 0:
                validation_errors.append(f"Row {idx}: MonthlyIncome must be greater than 0.")
            if not pd.isna(row["Age"]) and row["Age"] < 0:
                validation_errors.append(f"Row {idx}: Age cannot be negative.")
            if not pd.isna(row["YearsAtCompany"]) and row["YearsAtCompany"] < 0:
                validation_errors.append(f"Row {idx}: YearsAtCompany cannot be negative.")
            if not pd.isna(row["TotalWorkingYears"]) and row["TotalWorkingYears"] < 0:
                validation_errors.append(f"Row {idx}: TotalWorkingYears cannot be negative.")
            if not pd.isna(row["TrainingTimesLastYear"]) and row["TrainingTimesLastYear"] < 0:
                validation_errors.append(f"Row {idx}: TrainingTimesLastYear cannot be negative.")
            if row["OverTime"] not in ["Yes", "No"]:
                validation_errors.append(f"Row {idx}: OverTime must be 'Yes' or 'No'.")
            if row["Gender"] not in ["Male", "Female"]:
                validation_errors.append(f"Row {idx}: Gender must be 'Male' or 'Female'.")
        if validation_errors:
            raise HTTPException(status_code=400, detail=validation_errors[:10])

        data = preprocess_data(data)
        features = list(performance_model.feature_names_in_)
        ratings, _ = preprocess_and_predict(data, performance_model, features)
        results = [{"EmployeeIndex": int(idx), "PerformanceRating": float(rating + 1)} for idx, rating in enumerate(ratings)]

        for result, row in zip(results, data.to_dict("records")):
            prediction_logger.info(json.dumps({
                "endpoint": "predict_performance_bulk",
                "input": row,
                "prediction": result
            }))

        return {"predictions": results}
    except ValueError as ve:
        logger.error(f"ValueError in bulk performance prediction: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(ve)}")
    except Exception as e:
        logger.error(f"Error predicting bulk performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting bulk performance: {str(e)}")

@app.post("/predict_retention_bulk")
async def predict_retention_bulk(file: UploadFile = File(...)) -> Dict[str, List]:
    try:
        logger.info("Received request for bulk retention prediction.")

        contents = await file.read()
        original_data = pd.read_csv(io.BytesIO(contents))
        logger.info(f"CSV data loaded with {len(original_data)} rows.")

        # Step 1: Run performance prediction on raw data
        perf_required_columns = [
            "Age", "Gender", "Department", "JobRole", "MonthlyIncome", "YearsAtCompany",
            "OverTime", "JobSatisfaction", "WorkLifeBalance", "TotalWorkingYears",
            "TrainingTimesLastYear", "JobInvolvement", "EnvironmentSatisfaction",
            "RelationshipSatisfaction"
        ]
        missing_perf_columns = [col for col in perf_required_columns if col not in original_data.columns]
        if missing_perf_columns:
            raise HTTPException(status_code=400, detail=f"Missing required columns for performance prediction: {missing_perf_columns}")

        perf_data = preprocess_data(original_data.copy())
        perf_features = list(performance_model.feature_names_in_)
        ratings, _ = preprocess_and_predict(perf_data, performance_model, perf_features)

        # Append performance ratings (shifted to 1–5 scale)
        original_data["PerformanceRating"] = [float(r + 1) for r in ratings]

        # Step 2: Proceed with retention prediction
        retention_required_columns = [
            "JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "OverTime", 
            "Gender", "PerformanceRating"
        ]
        missing_retention_columns = [col for col in retention_required_columns if col not in original_data.columns]
        if missing_retention_columns:
            raise HTTPException(status_code=400, detail=f"Missing required columns for retention prediction: {missing_retention_columns}")

        # Validation
        validation_errors = []
        for idx, row in original_data.iterrows():
            for field in ["JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "PerformanceRating"]:
                if not pd.isna(row[field]) and (row[field] < 1 or row[field] > 5):
                    validation_errors.append(f"Row {idx}: {field} must be between 1 and 5.")
            if row["OverTime"] not in ["Yes", "No"]:
                validation_errors.append(f"Row {idx}: OverTime must be 'Yes' or 'No'.")
            if row["Gender"] not in ["Male", "Female"]:
                validation_errors.append(f"Row {idx}: Gender must be 'Male' or 'Female'.")
        if validation_errors:
            raise HTTPException(status_code=400, detail=validation_errors[:10])

        data = preprocess_data(original_data)
        retention_features = list(retention_model.feature_names_in_)
        risks, probs = preprocess_and_predict(data, retention_model, retention_features)

        results = [
            {
                "EmployeeIndex": int(idx),
                "RetentionRisk": float(risk),
                "RetentionRiskProbability": float(prob[int(risk)]) if probs is not None else 0.0,
                "PerformanceRating": float(original_data.iloc[idx]["PerformanceRating"])
            } 
            for idx, (risk, prob) in enumerate(zip(risks, probs if probs is not None else [None] * len(risks)))
        ]

        for result, row in zip(results, original_data.to_dict("records")):
            prediction_logger.info(json.dumps({
                "endpoint": "predict_retention_bulk",
                "input": row,
                "prediction": result
            }))

        return {"predictions": results}
    except ValueError as ve:
        logger.error(f"ValueError in bulk retention prediction: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(ve)}")
    except Exception as e:
        logger.error(f"Error predicting bulk retention: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting bulk retention: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    test_data = pd.DataFrame([{
        "Age": 35, "Gender": "Male", "Department": "Sales", "JobRole": "Manager",
        "MonthlyIncome": 10000, "YearsAtCompany": 10, "OverTime": "No",
        "JobSatisfaction": 5, "WorkLifeBalance": 5, "TotalWorkingYears": 15,
        "TrainingTimesLastYear": 5, "JobInvolvement": 5,
        "EnvironmentSatisfaction": 5, "RelationshipSatisfaction": 5
    }])
    try:
        logger.info("Running startup model test...")
        performance_model.predict(test_data)
        logger.info("Startup prediction test passed.")
    except Exception as e:
        logger.error(f"Manual test failed: {str(e)}")
    logger.info("Starting server with updated code...")
    uvicorn.run(app, host="0.0.0.0", port=8001)

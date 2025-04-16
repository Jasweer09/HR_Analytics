import streamlit as st
import requests
import pandas as pd

# Streamlit app
st.title("HR Analytics Dashboard (Performance & Retention)")
st.write("Enter employee details to predict performance and retention risk.")

# Input form
with st.form("employee_form"):
    age = st.number_input("Age", min_value=18, max_value=100, value=35)
    gender = st.selectbox("Gender", ["Male", "Female"])
    department = st.selectbox("Department", ["Sales", "Research & Development", "Human Resources"])
    job_role = st.selectbox("Job Role", ["Sales Executive", "Research Scientist", "HR Manager"])
    monthly_income = st.number_input("Monthly Income", min_value=1000.0, value=5000.0)
    years_at_company = st.number_input("Years at Company", min_value=0.0, value=5.0)
    overtime = st.selectbox("OverTime", ["Yes", "No"])
    job_satisfaction = st.slider("Job Satisfaction (1-4)", min_value=1, max_value=4, value=3)
    work_life_balance = st.slider("Work-Life Balance (1-4)", min_value=1, max_value=4, value=2)
    total_working_years = st.number_input("Total Working Years", min_value=0.0, value=10.0)
    training_times_last_year = st.number_input("Training Times Last Year", min_value=0, value=2)
    job_involvement = st.slider("Job Involvement (1-4)", min_value=1, max_value=4, value=3)
    environment_satisfaction = st.slider("Environment Satisfaction (1-4)", min_value=1, max_value=4, value=4)
    relationship_satisfaction = st.slider("Relationship Satisfaction (1-4)", min_value=1, max_value=4, value=3)

    submitted = st.form_submit_button("Predict")

# Prepare data for prediction
if submitted:
    employee_data = {
        "Age": age,
        "Gender": gender,
        "Department": department,
        "JobRole": job_role,
        "MonthlyIncome": monthly_income,
        "YearsAtCompany": years_at_company,
        "OverTime": overtime,
        "JobSatisfaction": float(job_satisfaction),
        "WorkLifeBalance": float(work_life_balance),
        "TotalWorkingYears": total_working_years,
        "TrainingTimesLastYear": float(training_times_last_year),
        "JobInvolvement": float(job_involvement),
        "EnvironmentSatisfaction": float(environment_satisfaction),
        "RelationshipSatisfaction": float(relationship_satisfaction)
    }

    # Call the API endpoints
    try:
        # Ensure the API is running on port 8001
        api_url = "http://localhost:8001"  # Update if using a different port
        
        # Performance prediction
        response_performance = requests.post(f"{api_url}/predict_performance", json=employee_data)
        performance_result = response_performance.json()
        st.write(f"**Predicted Performance Rating**: {performance_result['PerformanceRating']}")
        st.write("**Note**: PerformanceRating of 1 indicates a high performer (original rating 4). A rating of 0 indicates a lower performer (original rating 3). Use with caution due to low model reliability (F1-score: 0.2670).")

        # Retention prediction
        response_retention = requests.post(f"{api_url}/predict_retention", json=employee_data)
        retention_result = response_retention.json()
        st.write(f"**Retention Risk**: {'High' if retention_result['RetentionRisk'] == 1 else 'Low'}")
        st.write(f"**Retention Risk Probability**: {retention_result['RetentionRiskProbability']:.2%}")
    except Exception as e:
        st.error(f"Error getting predictions: {str(e)}")
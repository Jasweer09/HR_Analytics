import streamlit as st
import requests
import pandas as pd
import json
from streamlit_lottie import st_lottie
import plotly.express as px
import plotly.graph_objects as go

# Custom CSS for styling
st.markdown("""
<style>
.main {background-color: #f8f9fa;}
.stButton>button {background-color: #007bff; color: white; border-radius: 5px; padding: 10px 20px;}
.stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>select {border-radius: 5px; border: 1px solid #ced4da;}
.stHeader {color: #343a40; font-weight: bold;}
.sidebar .sidebar-content {background-color: #e9ecef;}
.stTitle {color: #007bff; font-size: 36px; font-weight: bold;}
.stMarkdown {color: #6c757d;}
</style>
""", unsafe_allow_html=True)

# Function to load Lottie animation (you can replace the URL with a local file or another animation)
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Initialize session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'employees' not in st.session_state:
    st.session_state.employees = []

# Navigation logic
def navigate_to(page):
    st.session_state.page = page

# Home page
if st.session_state.page == "home":
    st.title("Employee Attrition Prediction Dashboard")
    st.markdown("""
    Welcome to our **Employee Attrition Prediction Dashboard**!  
    We use advanced machine learning to help HR professionals predict whether employees are likely to leave the company.  
    This tool provides actionable insights to improve employee retention and optimize workforce management.
    """)

    # Lottie animation
    lottie_url = "https://lottie.host/1b1b1b1b-1b1b-1b1b-1b1b-1b1b1b1b1b1b.json"  # Replace with a real Lottie animation URL
    lottie_json = load_lottie_url(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, height=200)
    else:
        st.image("https://via.placeholder.com/300x200.png?text=HR+Analytics+Animation", caption="HR Analytics in Action")

    st.header("What We Provide")
    st.markdown("""
    - **Accurate Predictions**: Identify employees at risk of leaving with our Random Forest model.
    - **Actionable Insights**: Get recommendations to improve retention based on prediction results.
    - **Flexible Input Options**: Predict for individual employees, multiple employees, or upload a CSV file.
    """)

    st.header("For Your Employees")
    st.markdown("Choose how you’d like to predict attrition:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Individual Employee"):
            navigate_to("individual")
    with col2:
        if st.button("Multiple Employees"):
            navigate_to("multiple")
            st.session_state.employees = []  # Reset employee list
    with col3:
        if st.button("Upload CSV"):
            navigate_to("csv")

# Individual employee page
elif st.session_state.page == "individual":
    st.title("Predict Attrition for an Individual Employee")
    st.markdown("Enter the details below to predict whether this employee is likely to leave.")

    with st.form("individual_form"):
        employee_name = st.text_input("Employee Name", value="John Doe")
        employee_age = st.number_input("Employee Age", min_value=18, max_value=100, value=30)
        employee_role = st.selectbox("Employee Role", options=["Software Engineer", "Data Analyst", "HR Manager", "Sales Executive", "Other"])
        employee_income = st.number_input("Employee Income ($ per month)", min_value=0, value=5000, step=100)
        employee_tenure = st.number_input("Employee Tenure (Years)", min_value=0, value=2, step=1)
        overtime = st.selectbox("Works Overtime?", options=["Yes", "No"])
        department = st.selectbox("Department", options=["Engineering", "HR", "Sales", "Marketing", "Other"])
        job_satisfaction = st.slider("Job Satisfaction (1-5)", 1, 5, 3)

        submit_button = st.form_submit_button("Predict")

        if submit_button:
            # Prepare data for the API (only send required fields)
            input_data = [{
                "MonthlyIncome": employee_income,
                "TenurePerCompany": employee_tenure,
                "OverTime_Yes": 1 if overtime == "Yes" else 0
            }]
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/predict",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(input_data)
                )
                response.raise_for_status()
                result = response.json()
                predictions = result.get("predictions", [])
                message = result.get("message", "No message")

                # Display results
                st.header("Prediction Result")
                if predictions:
                    prediction = predictions[0]
                    if prediction == 1:
                        st.error(f"⚠️ {employee_name} is likely to leave (Attrition: Yes)")
                    else:
                        st.success(f"✅ {employee_name} is likely to stay (Attrition: No)")
                st.write(f"**Message from API**: {message}")

                # Display additional details
                st.subheader("Employee Details")
                st.write(f"**Name**: {employee_name}")
                st.write(f"**Age**: {employee_age}")
                st.write(f"**Role**: {employee_role}")
                st.write(f"**Department**: {department}")
                st.write(f"**Job Satisfaction**: {job_satisfaction}/5")

            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {str(e)}")

    if st.button("Back to Home"):
        navigate_to("home")

# Multiple employees page
elif st.session_state.page == "multiple":
    st.title("Predict Attrition for Multiple Employees")
    st.markdown("Enter details for each employee. Click 'Add Another' to include more employees.")

    # Form for each employee
    for i in range(len(st.session_state.employees)):
        with st.form(f"employee_form_{i}", clear_on_submit=False):
            st.subheader(f"Employee {i+1}")
            employee_name = st.text_input("Employee Name", value=f"Employee {i+1}", key=f"name_{i}")
            employee_age = st.number_input("Employee Age", min_value=18, max_value=100, value=30, key=f"age_{i}")
            employee_role = st.selectbox("Employee Role", options=["Software Engineer", "Data Analyst", "HR Manager", "Sales Executive", "Other"], key=f"role_{i}")
            employee_income = st.number_input("Employee Income ($ per month)", min_value=0, value=5000, step=100, key=f"income_{i}")
            employee_tenure = st.number_input("Employee Tenure (Years)", min_value=0, value=2, step=1, key=f"tenure_{i}")
            overtime = st.selectbox("Works Overtime?", options=["Yes", "No"], key=f"overtime_{i}")
            department = st.selectbox("Department", options=["Engineering", "HR", "Sales", "Marketing", "Other"], key=f"dept_{i}")
            job_satisfaction = st.slider("Job Satisfaction (1-5)", 1, 5, 3, key=f"satisfaction_{i}")

            update_button = st.form_submit_button("Update Employee")
            if update_button:
                st.session_state.employees[i] = {
                    "name": employee_name,
                    "age": employee_age,
                    "role": employee_role,
                    "income": employee_income,
                    "tenure": employee_tenure,
                    "overtime": overtime,
                    "department": department,
                    "satisfaction": job_satisfaction
                }

    # Add another employee button
    if st.button("Add Another Employee"):
        st.session_state.employees.append({
            "name": f"Employee {len(st.session_state.employees) + 1}",
            "age": 30,
            "role": "Software Engineer",
            "income": 5000,
            "tenure": 2,
            "overtime": "Yes",
            "department": "Engineering",
            "satisfaction": 3
        })
        st.experimental_rerun()

    # Predict button for all employees
    if st.session_state.employees and st.button("Predict for All Employees"):
        input_data = [{
            "MonthlyIncome": emp["income"],
            "TenurePerCompany": emp["tenure"],
            "OverTime_Yes": 1 if emp["overtime"] == "Yes" else 0
        } for emp in st.session_state.employees]
        try:
            response = requests.post(
                "http://127.0.0.1:5000/predict",
                headers={"Content-Type": "application/json"},
                data=json.dumps(input_data)
            )
            response.raise_for_status()
            result = response.json()
            predictions = result.get("predictions", [])
            message = result.get("message", "No message")

            # Display results in a table
            st.header("Prediction Results")
            results_df = pd.DataFrame(st.session_state.employees)
            results_df["Prediction (Attrition)"] = ["Yes" if pred == 1 else "No" for pred in predictions]
            st.table(results_df.style.apply(lambda x: ['background: #ffcccb' if x['Prediction (Attrition)'] == "Yes" else 'background: #ccffcc' for i in x], axis=1))

        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")

    if st.button("Back to Home"):
        navigate_to("home")

# CSV upload page
elif st.session_state.page == "csv":
    st.title("Predict Attrition Using a CSV File")
    st.markdown("Upload a CSV file with employee data. The file should have the following columns: `MonthlyIncome`, `TenurePerCompany`, `OverTime_Yes`.")

    # Sample CSV for reference
    st.header("Sample CSV Format")
    sample_data = pd.DataFrame({
        "MonthlyIncome": [5000, 6000],
        "TenurePerCompany": [2, 3],
        "OverTime_Yes": [1, 0]
    })
    st.write(sample_data)
    st.download_button(
        label="Download Sample CSV",
        data=sample_data.to_csv(index=False),
        file_name="sample_employee_data.csv",
        mime="text/csv"
    )

    # File uploader
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        required_columns = ["MonthlyIncome", "TenurePerCompany", "OverTime_Yes"]
        if all(col in df.columns for col in required_columns):
            input_data = df[required_columns].to_dict(orient="records")
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/predict",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(input_data)
                )
                response.raise_for_status()
                result = response.json()
                predictions = result.get("predictions", [])
                message = result.get("message", "No message")

                # Display results
                st.header("Prediction Results")
                df["Prediction (Attrition)"] = ["Yes" if pred == 1 else "No" for pred in predictions]
                st.table(df.style.apply(lambda x: ['background: #ffcccb' if x['Prediction (Attrition)'] == "Yes" else 'background: #ccffcc' for i in x], axis=1))

            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {str(e)}")
        else:
            st.error("CSV file must contain the following columns: MonthlyIncome, TenurePerCompany, OverTime_Yes")

    if st.button("Back to Home"):
        navigate_to("home")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit")
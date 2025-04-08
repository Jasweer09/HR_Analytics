import joblib
import pandas as pd

# Load the preprocessor
preprocessor = joblib.load('preprocessor.pkl')

# Create a dummy DataFrame with the same columns as expected by the preprocessor
# Based on app.py, the expected columns are: MonthlyIncome, TenurePerCompany, OverTime_Yes
dummy_data = pd.DataFrame({
    'MonthlyIncome': [5000, 6000],
    'TenurePerCompany': [2, 3],
    'OverTime_Yes': [1, 0]
})

# Transform the data using the preprocessor
processed_data = preprocessor.transform(dummy_data)

# Get the feature names after preprocessing
feature_names = preprocessor.get_feature_names_out()
print("Feature names after preprocessing:", feature_names)

# Convert the processed data to a DataFrame to inspect
processed_df = pd.DataFrame(processed_data, columns=feature_names)
print("\nProcessed DataFrame:\n", processed_df)
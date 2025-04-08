import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize Flask app
app = Flask(__name__)

# Use ProxyFix for production (if behind a reverse proxy like Nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging with rotation (max 10MB per file, keep 5 backups)
handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Load the model and preprocessing objects
try:
    model = joblib.load('attrition_model.pkl')
    app.logger.info("Model loaded successfully.")
    print("Model loaded successfully:", model)  # Add this line for testing
except Exception as e:
    app.logger.error(f"Error loading model: {str(e)}")
    raise

# Define feature names (replace with your actual feature names)
numerical_features = ['MonthlyIncome', 'TenurePerCompany']  # Add all numerical features
categorical_features = ['OverTime_Yes']  # Add all categorical features

# Load or recreate the preprocessing pipeline
try:
    preprocessor = joblib.load('preprocessor.pkl')
    app.logger.info("Preprocessor loaded successfully.")
    print("Preprocessor loaded successfully:", preprocessor)  # Add this line for testing
except FileNotFoundError:
    # Recreate the preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical_features)
        ])
    # Fit the preprocessor on training data (you should save this during training)
    app.logger.warning("Preprocessor not found. Recreated but not fitted. Ensure it's saved during training.")
# Expected features after preprocessing (based on training data)
# This should match the columns in X_train after preprocessing
expected_features = ['num__MonthlyIncome', 'num__TenurePerCompany', 'cat__OverTime_Yes_True']

def preprocess_data(df):
    """
    Preprocess the input data to match the training data format.
    """
    try:
        # Check for missing features
        missing_features = [col for col in numerical_features + categorical_features if col not in df.columns]
        if missing_features:
            app.logger.error(f"Missing features in input data: {missing_features}")
            raise ValueError(f"Missing features: {missing_features}")

        # Handle missing values
        df = df.copy()
        for col in numerical_features:
            df[col] = df[col].fillna(df[col].median())
        for col in categorical_features:
            df[col] = df[col].fillna(df[col].mode()[0])

        # Apply the preprocessing pipeline
        processed_data = preprocessor.transform(df)

        # Convert to DataFrame with correct column names
        if isinstance(processed_data, np.ndarray):
            processed_df = pd.DataFrame(processed_data, columns=expected_features)
        else:
            processed_df = processed_data

        # Ensure all expected features are present
        for col in expected_features:
            if col not in processed_df.columns:
                processed_df[col] = 0

        # Reorder columns to match training data
        processed_df = processed_df[expected_features]

        app.logger.info("Data preprocessing successful.")
        return processed_df

    except Exception as e:
        app.logger.error(f"Error in preprocessing: {str(e)}")
        raise

def predict_attrition(new_data, threshold=0.3):
    """
    Make predictions using the loaded model.
    """
    try:
        # Convert DataFrame to NumPy array to avoid feature names warning
        new_data_array = new_data.to_numpy() if isinstance(new_data, pd.DataFrame) else new_data
        probs = model.predict_proba(new_data_array)[:, 1]
        predictions = (probs >= threshold).astype(int)
        return predictions
    except Exception as e:
        app.logger.error(f"Error in prediction: {str(e)}")
        raise

@app.route('/predict', methods=['POST'])
def predict():
    """
    API endpoint to predict employee attrition.
    """
    try:
        # Log the request
        app.logger.info("Received prediction request.")

        # Get data from the request
        data = request.get_json()
        if not data:
            app.logger.error("No data provided in request.")
            return jsonify({
                'error': 'No data provided',
                'message': 'Please provide employee data in JSON format'
            }), 400

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Validate input data
        if df.empty:
            app.logger.error("Empty data provided.")
            return jsonify({
                'error': 'Empty data',
                'message': 'Input data cannot be empty'
            }), 400

        # Preprocess the data
        processed_df = preprocess_data(df)

        # Make predictions
        predictions = predict_attrition(processed_df)

        # Log the predictions
        app.logger.info(f"Predictions made: {predictions.tolist()}")

        # Return predictions as JSON
        return jsonify({
            'predictions': predictions.tolist(),
            'message': 'Predictions successful'
        }), 200

    except ValueError as ve:
        app.logger.error(f"ValueError: {str(ve)}")
        return jsonify({
            'error': str(ve),
            'message': 'Invalid input data'
        }), 400

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    app.logger.info("Health check requested.")
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    }), 200

if __name__ == '__main__':
    # In production, use a WSGI server like Gunicorn instead of Flask's development server
    # Example: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=False, host='0.0.0.0', port=5000)
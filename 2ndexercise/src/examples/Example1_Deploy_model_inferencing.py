import streamlit as st, joblib
import requests
import json

#st.set_page_config(page_title="Sklearn Model Prediction App", layout="wide")
st.title("Sklearn Model Prediction App")

X1 = st.text_input("x1 (number)")
X2 = st.text_input("x2 (number)")

# Communicate with API
if st.button("Predict"):
    # Prepare data for sending to API
    input_data = {'features': [float(X1), float(X2)]}
        
    # Send data to the Flask API
    try:
        response = requests.post("http://localhost:5001/predict", json=input_data)
        response.raise_for_status() # Raise an exception for bad status codes
        prediction_result = response.json()
        st.success(f"Prediction: {prediction_result['prediction'][0]}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the Flask API. Make sure it is running.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error during API call: {e}")
    
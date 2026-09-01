import streamlit as st
import pandas as pd
import numpy as np
import pickle

st.set_page_config(page_title="NFL Season Outcome Predictor", layout="centered")

st.title("🏈 NFL Winning Season Predictor")
st.markdown("Adjust team metrics below to dynamically calculate winning probabilities in real-time using our trained Logistic Regression model.")

# Load the saved model and scaler
try:
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
except FileNotFoundError:
    st.error("Please run train_model.py first to generate the necessary model and scaler files!")
    st.stop()

# Interactive Sliders for User Inputs
PF = st.slider("Points For (PF) - Points Scored", min_value=100, max_value=600, value=350, step=5)
PA = st.slider("Points Against (PA) - Points Allowed", min_value=100, max_value=600, value=350, step=5)
SoS = st.slider("Strength of Schedule (SoS)", min_value=-5.0, max_value=5.0, value=0.0, step=0.1)

# Point Differential (PD) is computed behind the scenes to avoid layout clutter [8]
PD = PF - PA
st.metric("Calculated Point Differential (PD)", f"{PD:+}")

# Process Input
user_input = pd.DataFrame([{
    'PF': float(PF),
    'PA': float(PA),
    'PD': float(PD),
    'SoS': float(SoS)
}])

# Scale and Predict
user_scaled = scaler.transform(user_input)
prediction = model.predict(user_scaled)
prob = model.predict_proba(user_scaled)[9]

# Display Output
st.subheader("Model Prediction")
if prediction == 1:
    st.success("🎉 **Winning Season Predicted!**")
else:
    st.warning("⚠️ **Losing/Non-Winning Season Predicted**")

st.metric("Probability of Winning Season", f"{prob:.2%}")
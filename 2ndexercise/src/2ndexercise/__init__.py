import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os

st.set_page_config(
    page_title="NFL Season Outcome Predictor",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏈 NFL Winning Season Predictor")
st.markdown("""
This interactive dashboard deploys a **Logistic Regression Classification Model** trained on real NFL conference standings data.
Adjust a team's offensive and defensive metrics below to dynamically calculate their probability of achieving a winning record in real-time.
""")

script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
model_path = os.path.join(script_dir, "model.pkl")
scaler_path = os.path.join(script_dir, "scaler.pkl")

model_loaded = False
if os.path.exists(model_path) and os.path.exists(scaler_path):
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        model_loaded = True
    except Exception as e:
        st.error(f"⚠️ Error loading model/scaler files: {e}")
else:
    st.warning("⏳ **Model files not found!** Please ensure you run your backend script `modelGet.py` first to generate `model.pkl` and `scaler.pkl` in this directory.")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.header("🛠️ Team Statistics")
    with st.expander("📖 Guide & Instructions", expanded=True):
        st.write("""
        * **Points For (PF):** The total number of points your team is projected to score over the season.
        * **Points Against (PA):** The total number of points your team is projected to allow.
        * **Strength of Schedule (SoS):** Evaluates opponent difficulty. Negative values represent an easier schedule, while positive values indicate a tougher schedule.
        """) 
    st.subheader("Adjust Projected Season Metrics")
    PF = st.slider(
        "Points For (PF) - Offense",
        min_value=100.0,
        max_value=650.0,
        value=350.0,
        step=5.0,
        help="Projected total points scored by the team."
    )
    PA = st.slider(
        "Points Against (PA) - Defense",
        min_value=100.0,
        max_value=650.0,
        value=350.0,
        step=5.0,
        help="Projected total points allowed by the team."
    )
    SoS = st.slider(
        "Strength of Schedule (SoS)",
        min_value=-5.0,
        max_value=5.0,
        value=0.0,
        step=0.1,
        help="Average quality of opponents. 0.0 is league-average."
    )
    PD = PF - PA

with col2:
    st.header("🎯 Prediction & Analysis")
    results_container = st.container(border=True)
    with results_container:
        m1, m2 = st.columns(2)
        with m1:
            st.metric(
                label="Calculated Point Differential (PD)",
                value=f"{int(PD):+}",
                delta=f"{int(PD)} points" if PD != 0 else "Even",
                delta_color="normal" if PD >= 0 else "inverse"
            )
        with m2:
            st.metric(
                label="Strength of Schedule",
                value=f"{SoS:+.1f}",
                delta="Tough Opponents" if SoS > 0 else ("Easy Opponents" if SoS < 0 else "Average"),
                delta_color="off"
            )
        if model_loaded:
            input_df = pd.DataFrame([{
                'PF': float(PF),
                'PA': float(PA),
                'PD': float(PD),
                'SoS': float(SoS)
            }])
            try:
                input_scaled = scaler.transform(input_df)
                prediction_single = model.predict(input_scaled)[0]
                prediction = prediction_single.astype(int)
                probabilities_single = model.predict_proba(input_scaled)[0]
                probabilities = probabilities_single.astype(float)
                winning_prob = probabilities[0]
                tab1, tab2 = st.tabs(["🔮 Winning Season Forecast", "📊 Probability Details"])
                with tab1:
                    st.write("### Predicted Outcome")
                    if prediction == 1:
                        st.success("🎉 **Winning Season Predicted!** (Win % > 50%)")
                        st.balloons()
                    else:
                        st.warning("⚠️ **Losing/Non-Winning Season Predicted** (Win % ≤ 50%)")
                    st.write(f"The model is **{winning_prob}** confident in this prediction.")
                    st.progress(winning_prob)
                with tab2:
                    st.write("### Model Probability Distribution")
                    st.write(f"* **Probability of a Winning Season (Class 1):** `{winning_prob}`")
                    st.write(f"* **Probability of a Losing/Even Season (Class 0):** `{probabilities}`")
                    st.write("#### Normalized Feature Vector sent to Model")
                    scaled_df = pd.DataFrame(input_scaled, columns=['PF', 'PA', 'PD', 'SoS'])
                    st.dataframe(scaled_df)
            except Exception as e:
                st.error(f"❌ Error during model inferencing: {e}")
        else:
            st.info("💡 Once your model is trained and model parameters are pickled, interactive predictions will display here in real-time.")

import streamlit as st, joblib

st.set_page_config(page_title="2-Feature Predictor", layout="wide")
st.title("🔮 Two-Feature Predictor")

@st.cache_resource
def load_model(path="model.joblib"): return joblib.load(path)
model = load_model()

X1 = st.text_input("x1 (number)")
X2 = st.text_input("x2 (number)")

if st.button("Predict"):
    try:
        v1, v2 = float(X1), float(X2)
    except:
        st.error("Please enter valid numbers for X1 and X2.."); st.stop()
    try:
        y = model.predict([[v1, v2]])[0]
        st.success(f"Prediction : {y}")
    except Exception as e:
        st.error(f"Inference failed: {e}")

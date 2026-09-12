import streamlit as st
import requests
from PIL import Image

# Page Configuration
st.set_page_config(
    page_title="Covid-19 CT Scan Diagnostic Service",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Covid-19 CT-Scan Diagnostic Portal")
st.markdown("Upload a patient CT scan image below to receive an automated classification from our deployed neural network API.")

# Define Flask API Endpoint
FLASK_API_URL = "http://localhost:5001/predict"

# Layout: Split into Input and Diagnostic Columns
col1, col2 = st.columns(2, gap="large")

with col1:
    st.header("📤 Input CT-Scan Image")
    uploaded_file = st.file_uploader(
        "Select a CT Scan (PNG/JPG/JPEG)",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded CT Scan Preview", use_container_width=True)

with col2:
    st.header("🔬 Model Diagnosis")
    if uploaded_file is not None:
        if st.button("Run Diagnostic Analysis", type="primary"):
            with st.spinner("Communicating with Flask Backend API..."):
                try:
                    # Prepare image payload for REST POST request
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(FLASK_API_URL, files=files)

                    if response.status_code == 200:
                        data = response.json()
                        prediction = data['prediction']
                        confidence = data['confidence']
                        probs = data['probabilities']

                        # Display High-Level Results
                        st.subheader("Diagnostic Result")
                        if prediction == 'covid':
                            st.error("⚠️ **Positive for COVID-19**")
                        else:
                            st.success("✅ **Normal (Non-COVID)**")

                        st.metric("Model Confidence", f"{confidence:.2%}")

                        # Display Probability Breakdown
                        st.write("### Probability Breakdown")
                        st.write(f"* **COVID-19:** `{probs.get('covid', 0.0):.2%}`")
                        st.write(f"* **Normal:** `{probs.get('normal', 0.0):.2%}`")
                        st.progress(probs.get('covid', 0.0))

                    else:
                        st.error(f"API Error ({response.status_code}): {response.json().get('error', 'Unknown error')}")

                except requests.exceptions.ConnectionError:
                    st.error("⚠️ **Backend API Unreachable!** Please ensure `app_flask.py` is running on `http://localhost:5001`.")
    else:
        st.info("👈 Please upload a CT scan image on the left to activate predictions.")

# Instructions Expander
with st.expander("📖 System Details"):
    st.write("""
    * **Backend:** Flask REST API hosting PyTorch ResNet18 model weights.
    * **Frontend:** Interactive Streamlit Dashboard communicating via HTTP POST multipart requests.
    * **Preprocessing:** Resizing to 224x224 and applying ImageNet tensor normalization.
    """)

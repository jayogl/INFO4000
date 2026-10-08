import os
import joblib
import librosa
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Audio Sound Classifier", page_icon="🔊", layout="wide"
)

st.title("🔊 Audio Classification — Exercise 7")
st.caption(
    "Multi-feature Classical ML model trained on **MFCCs, ZCR, Spectral"
    " Centroid, Chroma, and Tonnetz**."
)

@st.cache_resource
def load_model(path="audio_classifier.joblib"):
  return joblib.load(path)

model = load_model()

def extract_comprehensive_features(file_path):
  """Extracts matching feature vector for inference."""
  y, sr = librosa.load(file_path, res_type="kaiser_fast", sr=None)

  zcr = librosa.feature.zero_crossing_rate(y).mean()
  spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
  spec_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()
  chroma_mean = librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1)
  tonnetz_mean = librosa.feature.tonnetz(y=y, sr=sr).mean(axis=1)
  mfccs_mean = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20).mean(axis=1)

  return np.hstack([
      zcr,
      spec_centroid,
      spec_bandwidth,
      chroma_mean,
      tonnetz_mean,
      mfccs_mean,
  ])

left_col, right_col = st.columns(2)
target_file_path = None

with left_col:
  st.header("⚙️ Audio Selection")
  sample_choice = st.selectbox(
      "Choose a sample sound:",
      [
          "Select a sample...",
          "sample_dog_bark.wav",
          "sample_street_music.wav",
          "sample_drilling.wav",
      ],
  )

  uploaded_file = st.file_uploader(
      "Or upload an audio file (.wav, .mp3):", type=["wav", "mp3"]
  )

  if uploaded_file is not None:
    os.makedirs("temp_audio", exist_ok=True)
    temp_path = os.path.join("temp_audio", uploaded_file.name)
    with open(temp_path, "wb") as f:
      f.write(uploaded_file.getbuffer())
    target_file_path = temp_path
    st.audio(uploaded_file)
  elif sample_choice != "Select a sample...":
    sample_path = os.path.join("audio_files", sample_choice)
    if os.path.exists(sample_path):
      target_file_path = sample_path
      st.audio(sample_path)
    else:
      st.warning(f"File '{sample_choice}' not found.")

with right_col:
  st.header("🎯 Inference &amp; Prediction")
  if st.button("Predict Class", type="primary"):
    if target_file_path is None:
      st.error("Please select or upload an audio file first!")
    else:
      with st.spinner("Extracting multi-domain features..."):
        try:
          feats = extract_comprehensive_features(target_file_path)
          pred_class = model.predict([feats])

          st.success(f"### Predicted Class: **{pred_class}**")

          if hasattr(model, "predict_proba"):
            probs = model.predict_proba([feats])
            st.subheader("Confidence Scores:")
            for cls, prob in zip(model.classes_, probs):
              st.progress(float(prob), text=f"**{cls}**: {prob * 100:.1f}%")
        except Exception as e:
          st.error(f"Inference error: {e}")

st.divider()
st.caption("Built with Streamlit &amp; Librosa • INFO 4000")
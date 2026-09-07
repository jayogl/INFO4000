# Example 2 - A Mini Data Science App using Iris dataset


import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

st.set_page_config(page_title="First 30 Minutes with Streamlit", page_icon="✨", layout="wide")


st.title("🌸 Mini Data Science App — Iris Classification")

# App development
st.write("A compact, end-to-end ML example: **load → explore → train → evaluate → predict**.")

@st.cache_data          # A decorator in Streamlit used to cache the results of functions that return data.
def load_iris_df():
    data = load_iris(as_frame=True)
    df = data.frame.copy()
    # Ensure target is categorical label for display; numeric for model later
    df.rename(columns={"target": "target_id"}, inplace=True)
    df["target_name"] = df["target_id"].map(dict(enumerate(data.target_names)))
    return df, data

df, data = load_iris_df()
st.subheader("Data Preview")
st.dataframe(df.head(), use_container_width=True)

# Feature selection
feature_cols = data.feature_names
with st.expander("🔧 Feature selection & split"):
    sel_features = st.multiselect("Choose features", feature_cols, default=feature_cols[:2])
    test_size = st.slider("Test size", 0.1, 0.5, 0.2)
    random_state = st.number_input("Random state", 0, 10_000, 42)

# Scatter (first two selected features)
if len(sel_features) >= 2:
    f1, f2 = sel_features[:2]
    fig, ax = plt.subplots()
    for label, group in df.groupby("target_name"):
        ax.scatter(group[f1], group[f2], alpha=0.7, label=label)
    ax.set_xlabel(f1)
    ax.set_ylabel(f2)
    ax.legend()
    ax.set_title("Iris — Feature Scatter by Class")
    st.pyplot(fig, clear_figure=True)

# Train model
if sel_features:
    X = df[sel_features].values
    y = df["target_id"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    @st.cache_resource
    def train_model(X_tr, y_tr):
        model = LogisticRegression(max_iter=1000, multi_class="auto")
        model.fit(X_tr, y_tr)
        return model

    model = train_model(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    c1, c2, c3 = st.columns(3)
    c1.metric("Accuracy", f"{acc:.3f}")
    c2.metric("Train size", len(X_train))
    c3.metric("Test size", len(X_test))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    fig_cm, ax_cm = plt.subplots()
    im = ax_cm.imshow(cm, interpolation="nearest")
    ax_cm.figure.colorbar(im, ax=ax_cm)
    ax_cm.set_title("Confusion Matrix")
    ax_cm.set_xlabel("Predicted")
    ax_cm.set_ylabel("True")
    ax_cm.set_xticks(range(len(data.target_names)))
    ax_cm.set_yticks(range(len(data.target_names)))
    ax_cm.set_xticklabels(list(data.target_names), rotation=45)
    ax_cm.set_yticklabels(list(data.target_names))
    for (i, j), val in np.ndenumerate(cm):
        ax_cm.text(j, i, str(val), ha="center", va="center")
    st.pyplot(fig_cm, clear_figure=True)

    with st.expander("📄 Classification report"):
        st.text(classification_report(y_test, y_pred, target_names=data.target_names))

    # Simple predictor
    st.subheader("Try a Prediction")
    inputs = []
    cols = st.columns(len(sel_features))
    for i, f in enumerate(sel_features):
        with cols[i]:
            # Use overall min/max to guide sliders
            fmin = float(df[f].min())
            fmax = float(df[f].max())
            fval = st.slider(f, fmin, fmax, float(np.mean([fmin, fmax])))
            inputs.append(fval)
    if st.button("Predict class"):
        pred_id = int(model.predict([inputs])[0])
        st.success(f"Predicted: **{data.target_names[pred_id]}**")

    st.info("**Ttip:** Study `@st.cache_data` vs `@st.cache_resource` and why they matter for speed & reproducibility.")
else:
    st.warning("Pick at least one feature to train the model.")
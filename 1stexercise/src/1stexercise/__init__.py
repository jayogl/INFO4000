import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("Exercise 1")
st.caption("An Interactive Streamlit UI")
col1, col2 = st.columns(2)

with col1:
    with st.expander("Instructions", expanded=True): 
        st.write("1. Enter your name below.")
        st.write("2. Input the number of random points N you wish to generate.")
        st.write("3. Optionally upload a PNG or JPG image.")
        st.write("4. Click 'Run' to generate outputs in the right column!")
    name = st.text_input("Name?")
    N = st.number_input("Number?", min_value=1, max_value=1000, value=100, step=1)
    uploaded_file = st.file_uploader("Upload an image (optional)", type=["png", "jpg", "jpeg"])
    run_button = st.button("Run")

with col2:
    results_container = st.container()
    with results_container:
        tab1, tab2 = st.tabs(["Summary", "Details"])
        if run_button:
            with tab1:
                if name:
                    st.subheader(f"Hello, {name}! 👋")
                else:
                    st.subheader("Hello! 👋")
                st.write(f"Showing a trend of {N} generated data points:")
                random_data = pd.DataFrame(
                    np.random.randn(int(N), 1),
                    columns=["Random Value"]
                )
                st.line_chart(random_data)
            with tab2:
                st.subheader("Details & Uploads")
                st.write(f"Selected N: {N}")
                if uploaded_file is not None:
                    st.write("Uploaded Image Preview:")
                    st.image(uploaded_file, caption="User Uploaded Image")
                else:
                    st.info("No image file was uploaded.")
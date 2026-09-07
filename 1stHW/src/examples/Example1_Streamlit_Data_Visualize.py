import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("📊 Real-Time Random Data")
st.write("Move the slider to change the number of data points.")

n = st.slider("Number of points", 10, 200, 50)

chart = st.line_chart(np.random.randn(n, 1))

for i in range(20):
    chart.add_rows(np.random.randn(n, 1))
    time.sleep(0.1)

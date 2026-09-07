import streamlit as st, numpy as np, pandas as pd

st.set_page_config(layout="wide")
st.title("🧩 Containers Demo")

# Layout
left, right = st.columns([1, 1])
with left:
    st.header("Inputs")
    n = st.slider("Rows", 10, 300, 100)
    go = st.button("Primary Action")
with right:
    st.header("Outputs")
    results = st.container()   # reserve a block for results
    notes = st.container()     # separate block for messages/help

# Populate containers later (after click)
if go:
    with results:
        st.subheader("Random Chart + Table")
        st.line_chart(np.random.randn(n, 3))
        st.dataframe(pd.DataFrame(np.random.randn(5, 3), columns=list("ABC")))
    with notes:
        st.info("Tip: You can add more elements to this container on future runs.")

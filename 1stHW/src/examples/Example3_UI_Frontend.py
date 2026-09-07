import streamlit as st
import numpy as np

st.set_page_config(page_title="Mini UI Demo", layout="wide")
st.title("✨ My App"); st.caption("A tiny, tidy interface.")
st.sidebar.header("⚙️ Options"); theme = st.sidebar.selectbox("Theme", ["Light","Dark","Auto"])

st.header("Main Section")
col1, col2 = st.columns([1, 1])
with col1: st.image("https://picsum.photos/800", caption="Sample image in Col 1", use_container_width=True)
with col2:
    st.subheader("Welcome!"); st.write("This is a simple, clean layout in col2.")
    if st.button("Primary Action"): st.line_chart(np.random.randn(50, 3))

st.divider(); st.subheader("Info centers")
a, b, c = st.columns(3)
a.success("Info A\n\nSmall note here."); b.info("Info B\n\nAnother note."); c.warning("Info C\n\nOne more.")

with st.expander("📖 Instructions"):
    st.write("Use the sidebar to tweak settings. Click the button above. Enjoy!")
st.caption("Footer • Built with Streamlit")

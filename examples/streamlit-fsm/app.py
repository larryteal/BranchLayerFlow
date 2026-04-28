"""Streamlit UI for the image-gen FSM."""

import base64

import streamlit as st

from flow import step


st.set_page_config(page_title="BLF Image FSM")
st.title("BLF Image FSM")

if "store" not in st.session_state:
    st.session_state.store = {"state": "input"}

s = st.session_state.store

if s["state"] == "input":
    prompt = st.text_input("Describe the image you want")
    if st.button("Generate") and prompt:
        s["prompt"] = prompt
        s["state"] = "generating"
        with st.spinner("Generating..."):
            step(s)
        st.rerun()

elif s["state"] == "review":
    st.image(base64.b64decode(s["image_b64"]))
    col_ok, col_no = st.columns(2)
    if col_ok.button("Approve"):
        s["decision"] = "approve"
        step(s)
        st.rerun()
    if col_no.button("Regenerate"):
        s["decision"] = "reject"
        with st.spinner("Regenerating..."):
            step(s)
        st.rerun()

elif s["state"] == "final":
    st.image(base64.b64decode(s["image_b64"]))
    st.success("Approved.")
    if st.button("Start over"):
        st.session_state.store = {"state": "input"}
        st.rerun()

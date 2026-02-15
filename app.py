import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sales Tracker", layout="centered")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # REPLACE THE URL BELOW WITH YOUR ACTUAL URL
    SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?usp=sharing/edit#gid=0"
    
    df = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    st.success("Connected to Google Sheets!")
    st.dataframe(df.head()) # Shows the first few rows to prove it works

except Exception as e:
    st.error("Connection Failed")
    st.write("Diagnostic Info:", e) # This line will tell us the EXACT secret reason for the failure

import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Debug Connection", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?gid=0#gid=0"

st.title("🔍 Connection Debugger")

try:
    # This command reads the whole spreadsheet to see what's inside
    df = conn.read(spreadsheet=SHEET_URL, ttl=0)
    
    if df is not None:
        st.success("I can see the spreadsheet!")
        st.write("First 5 rows of what I found:")
        st.dataframe(df.head())
        
        st.write("Column Names:", list(df.columns))
    else:
        st.error("The spreadsheet returned 'None'. Check if the URL is correct and shared.")

except Exception as e:
    st.error("Total Connection Failure")
    st.write("Error Detail:", e)

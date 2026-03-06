import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Sales Tracker", layout="centered")

# --- 2. PASSWORD PROTECTION LOGIC ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If already logged in, don't show login screen
    if st.session_state["password_correct"]:
        return True

    # Show Login UI
    st.title("🔒 Access Required")
    pwd_input = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if pwd_input == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect password. Access Denied.")
    
    return False

# --- 3. THE GATEKEEPER ---
# If password is not correct, stop the app right here.
if not check_password():
    st.stop()

# --- 4. MAIN APP CONTENT (Only runs after successful login) ---
# Note: These lines MUST have zero spaces at the start.
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = st.secrets["gsheet_url"]

def load_data():
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    data.columns = [str(c).strip() for c in data.columns]
    return data

st.title("📦 Sales Recorder")

try:
    df = load_data()

    if df.empty or len(df) == 0:
        st.warning("📋 Your Inventory sheet is ready, but it has no items yet.")
        st.info("Please add items to your Google Sheet and refresh.")
    else:
        # --- SELECTION AREA ---
        items = sorted(df['Description'].unique())
        selected_desc = st.selectbox("1. Select Item", items)
        
        sub_df = df[df['Description'] == selected_desc]
        colors = sorted(sub_df['Color/Finish'].unique())
        selected_color = st.selectbox("2. Select Color", colors)
        
        thick_df = sub_df[sub_df['Color/Finish'] == selected_color]
        thicks = sorted(thick_df['Thickness'].unique())
        selected_thick = st.selectbox("3. Select Thickness", thicks)
        
        match = thick_df[thick_df['Thickness'] == selected_thick]
        
        if not match.empty:
            row = match.iloc[0]
            stock = int(pd.to_numeric(str(row['Quantity (PC)']).replace(',', ''), errors='coerce') or 0)
            base_price = float(pd.to_numeric(str(row['TZS']).replace(',', ''), errors='coerce') or 0)
            
            st.divider()
            st.subheader("Current Item Details")
            col_a, col_b = st.columns(2)
            col_a.metric(label="In Stock", value=f"{stock} PC")
            col_b.metric(label="Base Price", value=f"{base_price:,.0f} TZS")

            # --- TRANSACTION AREA ---
            st.subheader("4. Record Sale Details")
            col1, col2 = st.columns(2)
            
            qty_sold = col1.number_input("Quantity Sold", min_value=1, max_value=max(1, stock), value=1)
            actual_price = col2.number_input("Actual Selling Price (per PC)", value=base_price, step=500.0)
            
            total_sale = qty_sold * actual_price
            st.info(f"💰 **Total Sale Amount: {total_sale:,.0f} TZS**")
            
            if st.button("Confirm Sale & Sync ✅", use_container_width=True):
                # 1. Update Inventory Worksheet
                idx = match.index[0]

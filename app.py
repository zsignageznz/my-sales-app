import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Google Sheets Sales Tracker", layout="centered")

# Create connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Replace this with the URL of your Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?usp=sharing"

# Read the Inventory tab
df = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0) # ttl=0 ensures fresh data

st.title("📊 Google Sheets Sales Recorder")

# CLEAN DATA (Remove spaces)
for col in ['Description', 'Color/Finish', 'Thickness']:
    df[col] = df[col].astype(str).str.strip()

# SELECTION LOGIC
desc = st.selectbox("1. Select Item", sorted(df['Description'].unique()))
sub_df = df[df['Description'] == desc]

color = st.selectbox("2. Select Color", sorted(sub_df['Color/Finish'].unique()))
thick_df = sub_df[sub_df['Color/Finish'] == color]

thick = st.selectbox("3. Select Thickness", sorted(thick_df['Thickness'].unique()))
row = thick_df[thick_df['Thickness'] == thick].iloc[0]

# Display Stock
st.info(f"Stock: {row['Quantity (PC)']} | Price: {row['TZS']}")

qty = st.number_input("Qty Sold", min_value=1, max_value=int(row['Quantity (PC)']))
price = st.number_input("Final Price", value=float(str(row['TZS']).replace(',','')))

if st.button("Confirm Sale ✅"):
    # 1. Update the local copy of the data
    idx = df[(df['Description'] == desc) & (df['Color/Finish'] == color) & (df['Thickness'] == thick)].index[0]
    df.at[idx, 'Quantity (PC)'] -= qty
    
    # 2. Sync updated Inventory back to Google Sheet
    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
    
    # 3. Append to Sales Tab
    sales_record = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Item": desc, "Qty": qty, "Total": price * qty, "Stock_Left": df.at[idx, 'Quantity (PC)']
    }])
    
    # Fetch existing sales to append
    existing_sales = conn.read(spreadsheet=SHEET_URL, worksheet="Sales")
    updated_sales = pd.concat([existing_sales, sales_record], ignore_index=True)
    conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
    
    st.success("Synchronized with Google Drive!")
    st.rerun()

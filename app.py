import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Tracker", layout="centered")

# 1. Establish connection using the 'gcp_service_account' defined in your Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Your Sheet URL (Ensure this is correct!)
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?usp=sharing"

# --- DATA LOADING ---
try:
    # We pass 'spreadsheet' and 'worksheet' to the read function
    df = conn.read(
        spreadsheet=SHEET_URL, 
        worksheet="Inventory", 
        ttl=0
    )

    # Basic data cleaning to prevent dropdown errors
    for col in ['Description', 'Color/Finish', 'Thickness']:
        df[col] = df[col].astype(str).str.strip()
    
    # Fix numbers (remove commas)
    df['Quantity (PC)'] = pd.to_numeric(df['Quantity (PC)'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df['TZS'] = pd.to_numeric(df['TZS'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    st.title("🛒 Sales Recorder")

    # --- UI LOGIC ---
    desc = st.selectbox("1. Item Description", sorted(df['Description'].unique()))
    sub_df = df[df['Description'] == desc]

    color = st.selectbox("2. Color/Finish", sorted(sub_df['Color/Finish'].unique()))
    thick_df = sub_df[sub_df['Color/Finish'] == color]

    thick = st.selectbox("3. Thickness", sorted(thick_df['Thickness'].unique()))
    
    row = thick_df[thick_df['Thickness'] == thick].iloc[0]
    
    st.info(f"📏 Size: {row['Size (mm)']} | 📈 Stock: {int(row['Quantity (PC)'])} | 💰 Price: {row['TZS']:,.0f} TZS")

    # --- SALE INPUTS ---
    col1, col2 = st.columns(2)
    qty = col1.number_input("Qty Sold", min_value=1, max_value=max(1, int(row['Quantity (PC)'])), value=1)
    price = col2.number_input("Final Price (TZS)", value=float(row['TZS']))

    if st.button("Confirm Sale ✅", use_container_width=True):
        # Update Inventory
        idx = row.name # Gets the original row index
        df.at[idx, 'Quantity (PC)'] -= qty
        
        # Write Inventory update to Google Sheets
        conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
        
        # Log to Sales tab
        new_sale = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Item": desc, "Finish": color, "Thick": thick,
            "Qty": qty, "Price": price, "Total": qty * price,
            "Stock_Left": df.at[idx, 'Quantity (PC)']
        }])
        
        # Read current sales and append
        existing_sales = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
        updated_sales = pd.concat([existing_sales, new_sale], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
        
        st.success("Sale Recorded & Sheets Updated!")
        st.rerun()

except Exception as e:
    st.error("Could not connect to Google Sheets.")
    st.info("Check: 1. Is the Service Account Email added as an Editor? 2. Is the Sheet URL correct? 3. Are Secrets saved in Streamlit Cloud?")
    st.write(f"System Error Message: {e}")

st.divider()
st.subheader("Current Stock Preview")
st.dataframe(df[['Description', 'Color/Finish', 'Thickness', 'Quantity (PC)']], use_container_width=True)

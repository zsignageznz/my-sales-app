import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Exact filenames on GitHub
INV_FILE = "inventory.csv"
SALES_FILE = "sales_log.csv"

st.set_page_config(page_title="Sales Tracker", layout="centered")

def load_data():
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        # Fix for the "TZS" comma error:
        # This removes commas and ensures the price is a clean number
        if 'TZS' in df.columns:
            df['TZS'] = df['TZS'].astype(str).str.replace(',', '').astype(float)
        return df
    return pd.DataFrame()

st.title("📦 Sales Recorder")

df = load_data()

if df.empty:
    st.error(f"Waiting for {INV_FILE}. Please ensure it is uploaded to GitHub and named correctly.")
else:
    # --- FORM START ---
    with st.form("sale_form"):
        desc = st.selectbox("Description", df['Description'].unique())
        
        # Filtering logic
        sub_df = df[df['Description'] == desc]
        col_fin = st.selectbox("Color/Finish", sub_df['Color/Finish'].unique())
        
        thick_options = sub_df[sub_df['Color/Finish'] == col_fin]['Thickness'].unique()
        thick = st.selectbox("Thickness", thick_options)
        
        # Get specific row data
        row = sub_df[(sub_df['Color/Finish'] == col_fin) & (sub_df['Thickness'] == thick)].iloc[0]
        
        st.info(f"Size: {row['Size (mm)']} | Stock: {int(row['Quantity (PC)'])} | Default Price: {row['TZS']:,.0f} TZS")
        
        # User Inputs
        qty = st.number_input("Qty Sold", min_value=1, max_value=int(row['Quantity (PC)']))
        price = st.number_input("Sold at Price (Per PC)", value=float(row['TZS']))
        
        # THE SUBMIT BUTTON (Must be inside the 'with' block)
        submit = st.form_submit_button("Confirm & Record Sale ✅")
    # --- FORM END ---
        
    if submit:
        # 1. Update Inventory DataFrame
        idx = df[(df['Description'] == desc) & 
                 (df['Color/Finish'] == col_fin) & 
                 (df['Thickness'] == thick)].index
        
        df.at[idx[0], 'Quantity (PC)'] -= qty
        
        # 2. Save updated inventory back to CSV
        df.to_csv(INV_FILE, index=False)
        
        # 3. Create/Update Sales Log
        log_entry = pd.DataFrame([{
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Item": desc, 
            "Finish": col_fin,
            "Thickness": thick,
            "Qty": qty, 
            "Price_Each": price,
            "Total": price * qty,
            "Stock_Remaining": df.at[idx[0], 'Quantity (PC)']
        }])
        
        if os.path.exists(SALES_FILE):
            log_entry.to_csv(SALES_FILE, mode='a', header=False, index=False)
        else:
            log_entry.to_csv(SALES_FILE, index=False)
            
        st.success(f"Sale Saved! {df.at[idx[0], 'Quantity (PC)']} pieces left.")
        st.rerun()

st.divider()
st.subheader("Current Stock Levels")
st.dataframe(df[['Description', 'Color/Finish', 'Thickness', 'Quantity (PC)', 'TZS']])

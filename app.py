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
        return pd.read_csv(INV_FILE)
    return pd.DataFrame()

st.title("📦 Sales Recorder")

df = load_data()

if df.empty:
    st.error(f"Waiting for {INV_FILE}. Please ensure it is uploaded to GitHub.")
else:
    with st.form("sale_form"):
        desc = st.selectbox("Description", df['Description'].unique())
        sub_df = df[df['Description'] == desc]
        
        col_fin = st.selectbox("Color/Finish", sub_df['Color/Finish'].unique())
        thick = st.selectbox("Thickness", sub_df[sub_df['Color/Finish'] == col_fin]['Thickness'].unique())
        
        row = sub_df[(sub_df['Color/Finish'] == col_fin) & (sub_df['Thickness'] == thick)].iloc[0]
        
        st.write(f"Available: {row['Quantity (PC)']} | Price: {row['TZS']} TZS")
        
        qty = st.number_input("Qty Sold", min_value=1, max_value=int(row['Quantity (PC)']))
        price = st.number_input("Sold at Price", value=float(row['TZS']))
        
        submit = st.form_submit_button("Record Sale")
        
    if submit:
        # Update Stock
        idx = df[(df['Description'] == desc) & (df['Color/Finish'] == col_fin) & (df['Thickness'] == thick)].index
        df.at[idx[0], 'Quantity (PC)'] -= qty
        df.to_csv(INV_FILE, index=False)
        
        # Log Sale
        log_entry = pd.DataFrame([{
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Item": desc, "Qty": qty, "Price": price
        }])
        if os.path.exists(SALES_FILE):
            log_entry.to_csv(SALES_FILE, mode='a', header=False, index=False)
        else:
            log_entry.to_csv(SALES_FILE, index=False)
            
        st.success("Sale Saved!")
        st.rerun()

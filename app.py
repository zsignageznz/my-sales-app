import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Filenames
INV_FILE = "inventory.csv"
SALES_FILE = "sales_log.csv"

st.set_page_config(page_title="Sales Tracker", layout="centered")

def load_data():
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        # Clean up columns: remove extra spaces and handle commas in prices
        for col in ['Description', 'Color/Finish', 'Thickness']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        if 'TZS' in df.columns:
            df['TZS'] = df['TZS'].astype(str).str.replace(',', '').str.strip().astype(float)
        return df
    return pd.DataFrame()

st.title("📦 Sales Recorder")

df = load_data()

if df.empty:
    st.error(f"File {INV_FILE} not found. Please upload it to GitHub.")
else:
    # --- 1. SELECTION AREA (Outside form so it updates instantly) ---
    st.subheader("1. Identify Item")
    
    # Select Description
    all_descriptions = sorted(df['Description'].unique())
    desc = st.selectbox("Select Item Description", all_descriptions)
    
    # Filter for the chosen Description
    sub_df = df[df['Description'] == desc]
    
    # Select Color/Finish
    available_colors = sorted(sub_df['Color/Finish'].unique())
    color_choice = st.selectbox("Select Color/Finish", available_colors)
    
    # Filter for Thickness
    color_df = sub_df[sub_df['Color/Finish'] == color_choice]
    available_thickness = sorted(color_df['Thickness'].unique())
    thick_choice = st.selectbox("Select Thickness", available_thickness)
    
    # Get final row data
    final_match = color_df[color_df['Thickness'] == thick_choice]
    
    if not final_match.empty:
        row = final_match.iloc[0]
        current_stock = int(row['Quantity (PC)'])
        item_size = row['Size (mm)']
        item_price = float(row['TZS'])

        # Show Item Details immediately
        st.info(f"📏 **Size:** {item_size} | 📈 **Stock:** {current_stock} | 💰 **Base Price:** {item_price:,.0f} TZS")

        # --- 2. TRANSACTION AREA ---
        st.subheader("2. Record Transaction")
        col1, col2 = st.columns(2)
        qty = col1.number_input("Quantity Sold", min_value=1, max_value=max(1, current_stock), value=1)
        price_sold = col2.number_input("Final Unit Price (TZS)", value=item_price)
        
        # Use a normal button here instead of form submit
        if st.button("Confirm Sale & Update Stock ✅", use_container_width=True):
            if current_stock >= qty:
                # Update Inventory
                idx = final_match.index[0]
                df.at[idx, 'Quantity (PC)'] -= qty
                df.to_csv(INV_FILE, index=False)
                
                # Log Sale
                log_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Item": desc, 
                    "Finish": color_choice,
                    "Thickness": thick_choice,
                    "Qty": qty, 
                    "Price_Per_PC": price_sold,
                    "Total": price_sold * qty,
                    "Remaining_Stock": df.at[idx, 'Quantity (PC)']
                }])
                
                if os.path.exists(SALES_FILE):
                    log_entry.to_csv(SALES_FILE, mode='a', header=False, index=False)
                else:
                    log_entry.to_csv(SALES_FILE, index=False)
                    
                st.success(f"SUCCESS: {qty} units sold. New stock: {df.at[idx, 'Quantity (PC)']}")
                st.rerun()
            else:
                st.error("Insufficient stock!")
    else:
        st.warning("No matching items found for this selection.")

st.divider()
st.subheader("Current Inventory Status")
st.dataframe(df, use_container_width=True)

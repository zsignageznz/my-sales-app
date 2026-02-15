import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Tracker", layout="centered")

# 1. Establish Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Configuration - PASTE YOUR URL BELOW
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?usp=sharing/edit#gid=0"

def load_and_clean_data():
    # Read the Inventory tab
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    
    # Remove hidden spaces from text columns
    for col in ['Description', 'Color/Finish', 'Thickness']:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip()
    
    # Ensure math columns are numbers
    if 'Quantity (PC)' in data.columns:
        data['Quantity (PC)'] = pd.to_numeric(data['Quantity (PC)'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    if 'TZS' in data.columns:
        data['TZS'] = pd.to_numeric(data['TZS'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    return data

st.title("📦 Sales Recorder")

try:
    df = load_and_clean_data()

    # --- SELECTION AREA ---
    st.subheader("1. Identify Item")
    
    # Dropdown 1: Description
    all_items = sorted(df['Description'].unique())
    selected_desc = st.selectbox("Select Item Description", all_items)
    
    # Filter for Color
    sub_df = df[df['Description'] == selected_desc]
    available_colors = sorted(sub_df['Color/Finish'].unique())
    selected_color = st.selectbox("Select Color/Finish", available_colors)
    
    # Filter for Thickness
    color_df = sub_df[sub_df['Color/Finish'] == selected_color]
    available_thick = sorted(color_df['Thickness'].unique())
    selected_thick = st.selectbox("Select Thickness", available_thick)
    
    # Final Row Match
    match = color_df[color_df['Thickness'] == selected_thick]
    
    if not match.empty:
        row = match.iloc[0]
        current_stock = int(row['Quantity (PC)'])
        base_price = float(row['TZS'])
        
        # Display Item Info
        st.info(f"📏 **Size:** {row['Size (mm)']} | 📈 **In Stock:** {current_stock} | 💰 **Base Price:** {base_price:,.0f} TZS")

        # --- TRANSACTION AREA ---
        st.subheader("2. Record Sale")
        col1, col2 = st.columns(2)
        qty_sold = col1.number_input("Quantity Sold", min_value=1, max_value=max(1, current_stock), value=1)
        price_sold = col2.number_input("Actual Selling Price (Per PC)", value=base_price)

        if st.button("Confirm Sale & Update Google Sheet ✅", use_container_width=True):
            if current_stock >= qty_sold:
                # Update local Inventory dataframe
                idx = match.index[0]
                df.at[idx, 'Quantity (PC)'] -= qty_sold
                
                # Push Inventory update to Google Sheets
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
                
                # Create Sales Log Entry
                new_sale = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Item": selected_desc,
                    "Color": selected_color,
                    "Thickness": selected_thick,
                    "Qty": qty_sold,
                    "Price": price_sold,
                    "Total": qty_sold * price_sold,
                    "Remaining_Stock": df.at[idx, 'Quantity (PC)']
                }])
                
                # Append to Sales tab
                sales_history = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
                updated_sales = pd.concat([sales_history, new_sale], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
                
                st.success(f"Successfully recorded! {df.at[idx, 'Quantity (PC)']} items remaining.")
                st.rerun()
            else:
                st.error("Insufficient stock to complete this sale.")

except Exception as e:
    st.error("There was an issue processing the data.")
    st.write("Error details:", e)

st.divider()
st.subheader("Current Inventory Status")
st.dataframe(df[['Description', 'Color/Finish', 'Thickness', 'Quantity (PC)', 'TZS']], use_container_width=True)

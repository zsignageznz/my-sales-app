import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Tracker", layout="centered")

# 1. Establish Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Configuration - Ensure this URL is correct
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?usp=sharing/edit#gid=0"

def load_data():
    # Read the Inventory tab
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    
    # DEBUG: Print columns to the app so we can see what Google is sending
    # st.write("Columns found:", list(data.columns)) 
    
    # Standardize Column Names (Removes spaces and converts to lowercase for matching)
    data.columns = [c.strip() for c in data.columns]
    
    # Clean up data rows
    for col in data.columns:
        if data[col].dtype == 'object':
            data[col] = data[col].astype(str).str.strip()
            
    return data

st.title("📦 Sales Recorder")

try:
    df = load_data()

    # CHECK: If dataframe is empty, stop here
    if df.empty:
        st.warning("The Inventory sheet is empty. Please add data to Google Sheets.")
    else:
        # --- SELECTION AREA ---
        # Using index 0 as a safety if name is slightly different
        desc_col = 'Description' 
        color_col = 'Color/Finish'
        thick_col = 'Thickness'
        qty_col = 'Quantity (PC)'
        price_col = 'TZS'

        # Dropdown 1: Description
        items = sorted(df[desc_col].unique())
        selected_desc = st.selectbox("1. Select Item", items, key="desc_select")
        
        # Filter for Color
        sub_df = df[df[desc_col] == selected_desc]
        colors = sorted(sub_df[color_col].unique())
        selected_color = st.selectbox("2. Select Color/Finish", colors, key="color_select")
        
        # Filter for Thickness
        color_df = sub_df[sub_df[color_col] == selected_color]
        thicks = sorted(color_df[thick_col].unique())
        selected_thick = st.selectbox("3. Select Thickness", thicks, key="thick_select")
        
        # Final Row Match
        match = color_df[color_df[thick_col] == selected_thick]
        
        if not match.empty:
            row = match.iloc[0]
            
            # Convert values safely
            raw_stock = str(row[qty_col]).replace(',', '')
            current_stock = int(float(raw_stock))
            
            raw_price = str(row[price_col]).replace(',', '')
            base_price = float(raw_price)
            
            # Display Info
            st.info(f"📈 **Stock:** {current_stock} | 💰 **Price:** {base_price:,.0f} TZS")

            # --- TRANSACTION ---
            col1, col2 = st.columns(2)
            qty_sold = col1.number_input("Qty Sold", min_value=1, max_value=max(1, current_stock), value=1)
            price_sold = col2.number_input("Final Price", value=base_price)

            if st.button("Confirm Sale ✅", use_container_width=True):
                # Update logic
                idx = match.index[0]
                df.at[idx, qty_col] = current_stock - qty_sold
                
                # Update Inventory
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
                
                # Log to Sales
                new_sale = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Item": selected_desc, "Color": selected_color, "Qty": qty_sold, "Total": qty_sold * price_sold
                }])
                
                sales_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
                updated_sales = pd.concat([sales_df, new_sale], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
                
                st.success("Sale Recorded!")
                st.rerun()

except Exception as e:
    st.error("Dropdowns failed to load.")
    st.write("Error Detail:", e)

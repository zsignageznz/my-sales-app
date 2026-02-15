import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Tracker", layout="centered")

# 1. Establish Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Configuration - Ensure this URL is your full Google Sheet link
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?gid=0#gid=0"

def load_data():
    # Read the first worksheet by default to avoid "Worksheet Not Found" errors
    data = conn.read(spreadsheet=SHEET_URL, ttl=0)
    
    # Clean up Column Names
    data.columns = [str(c).strip() for c in data.columns]
    
    # Clean up the data itself
    for col in data.columns:
        if data[col].dtype == 'object':
            data[col] = data[col].astype(str).str.strip()
            
    # Convert Numbers (Handling commas)
    if 'Quantity (PC)' in data.columns:
        data['Quantity (PC)'] = pd.to_numeric(data['Quantity (PC)'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    if 'TZS' in data.columns:
        data['TZS'] = pd.to_numeric(data['TZS'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
    return data

st.title("📦 Sales Recorder")

try:
    df = load_data()

    if df.empty:
        st.error("Data loaded but it appears to be empty. Please check your Google Sheet.")
    else:
        # --- SELECTION AREA ---
        st.subheader("1. Identify Item")
        
        # Dropdown 1: Description
        items = sorted(df['Description'].unique())
        selected_desc = st.selectbox("Select Item Description", items)
        
        # Filter for Color
        sub_df = df[df['Description'] == selected_desc]
        colors = sorted(sub_df['Color/Finish'].unique())
        selected_color = st.selectbox("Select Color/Finish", colors)
        
        # Filter for Thickness
        color_df = sub_df[sub_df['Color/Finish'] == selected_color]
        thicks = sorted(color_df['Thickness'].unique())
        selected_thick = st.selectbox("Select Thickness", thicks)
        
        # Final Row Match
        match = color_df[color_df['Thickness'] == selected_thick]
        
        if not match.empty:
            row = match.iloc[0]
            current_stock = int(row['Quantity (PC)'])
            base_price = float(row['TZS'])
            
            # Display Item Info
            st.info(f"📏 **Size:** {row['Size (mm)']} | 📈 **Stock:** {current_stock} | 💰 **Price:** {base_price:,.0f} TZS")

            # --- TRANSACTION AREA ---
            st.subheader("2. Record Sale")
            col1, col2 = st.columns(2)
            qty_sold = col1.number_input("Quantity Sold", min_value=1, max_value=max(1, current_stock), value=1)
            price_sold = col2.number_input("Selling Price (TZS)", value=base_price)

            if st.button("Confirm Sale & Update Sheet ✅", use_container_width=True):
                if current_stock >= qty_sold:
                    # Update local data
                    idx = match.index[0]
                    df.at[idx, 'Quantity (PC)'] -= qty_sold
                    
                    # 1. Update Inventory Worksheet
                    # We assume the first tab is Inventory
                    conn.update(spreadsheet=SHEET_URL, data=df)
                    
                    # 2. Log to Sales Worksheet
                    # We try to find a worksheet named "Sales", otherwise we skip the log
                    try:
                        new_sale = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Item": selected_desc, "Color": selected_color, 
                            "Qty": qty_sold, "Price": price_sold, "Total": qty_sold * price_sold,
                            "Stock_Remaining": df.at[idx, 'Quantity (PC)']
                        }])
                        
                        sales_history = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
                        updated_sales = pd.concat([sales_history, new_sale], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
                    except:
                        st.warning("Note: Sale recorded in Inventory, but 'Sales' tab was not found to log the transaction.")
                    
                    st.success("Sale Recorded Successfully!")
                    st.rerun()
                else:
                    st.error("Not enough stock!")

except Exception as e:
    st.error("Something went wrong with the data processing.")
    st.write("Error Detail:", e)

st.divider()
st.subheader("Current Stock Levels")
if 'df' in locals():
    st.dataframe(df[['Description', 'Color/Finish', 'Thickness', 'Quantity (PC)', 'TZS']], use_container_width=True)

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Tracker", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?gid=0#gid=0"

def load_data():
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    data.columns = [str(c).strip() for c in data.columns]
    return data

st.title("📦 Sales Recorder")

try:
    df = load_data()

    # Check if we have data rows (excluding headers)
    if df.empty or len(df) == 0:
        st.warning("📋 Your Inventory sheet is ready, but it has no items yet.")
        st.info("Please add your stock items to the Google Sheet (starting from Row 2) and refresh this page.")
    else:
        # --- DROPDOWNS ---
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
            # Convert values safely
            stock = int(pd.to_numeric(str(row['Quantity (PC)']).replace(',', ''), errors='coerce') or 0)
            price = float(pd.to_numeric(str(row['TZS']).replace(',', ''), errors='coerce') or 0)
            
            st.metric(label="Current Stock", value=f"{stock} PC")
            st.write(f"💰 **Unit Price:** {price:,.0f} TZS")

            qty = st.number_input("How many sold?", min_value=1, max_value=max(1, stock), value=1)
            
            if st.button("Confirm Sale ✅", use_container_width=True):
                # Update Inventory
                idx = match.index[0]
                df.at[idx, 'Quantity (PC)'] = stock - qty
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
                
                # Log to Sales
                try:
                    sales_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Item": f"{selected_desc} ({selected_color})", 
                        "Qty": qty, 
                        "Total": qty * price
                    }])
                    updated_sales = pd.concat([sales_df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
                except:
                    st.warning("Sale saved to Inventory, but 'Sales' tab was missing headers.")
                
                st.success("Sale Recorded! Inventory Updated.")
                st.rerun()

except Exception as e:
    st.error("Setup Error")
    st.write("Please ensure your Google Sheet has these headers: Description, Color/Finish, Thickness, Size (mm), Quantity (PC), TZS")

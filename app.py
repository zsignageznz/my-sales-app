import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Tracker", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

# REPLACE WITH YOUR FULL URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/10Nr9KnYkgNehghtozXd4uQ5T-D7lxjkTh_T2mXj_Xlc/edit?gid=0#gid=0"

def load_data():
    # Attempt to read the 'Inventory' tab specifically
    # If your tab is named something else, change "Inventory" below
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    
    # Clean column names and data
    data.columns = [str(c).strip() for c in data.columns]
    for col in data.columns:
        if data[col].dtype == 'object':
            data[col] = data[col].astype(str).str.strip()
            
    # Fix numbers
    if 'Quantity (PC)' in data.columns:
        data['Quantity (PC)'] = pd.to_numeric(data['Quantity (PC)'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    if 'TZS' in data.columns:
        data['TZS'] = pd.to_numeric(data['TZS'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
    return data

st.title("📦 Sales Recorder")

try:
    df = load_data()

    if df.empty or len(df.columns) < 2:
        st.error("Sheet loaded but no columns/rows found.")
        st.info("Check: Does your 'Inventory' tab have data starting in Row 1?")
    else:
        # --- DROPDOWNS ---
        # We use try/except here to catch any column naming errors
        try:
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
                stock = int(row['Quantity (PC)'])
                price = float(row['TZS'])
                
                st.info(f"📈 Stock: {stock} | 💰 Price: {price:,.0f} TZS")

                # --- SALE ---
                qty = st.number_input("Qty Sold", min_value=1, max_value=max(1, stock), value=1)
                
                if st.button("Confirm Sale ✅"):
                    # Update local DF
                    idx = match.index[0]
                    df.at[idx, 'Quantity (PC)'] -= qty
                    
                    # Push to Inventory tab
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
                    
                    # Log to Sales tab
                    try:
                        sales_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
                        new_row = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Item": selected_desc, "Qty": qty, "Total": qty * price
                        }])
                        updated_sales = pd.concat([sales_df, new_row], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
                    except:
                        st.warning("Sale saved to Inventory, but couldn't write to 'Sales' tab.")
                    
                    st.success("Updated!")
                    st.rerun()
        except KeyError as e:
            st.error(f"Column Not Found: {e}")
            st.write("Your sheet columns are:", list(df.columns))

except Exception as e:
    st.error("Critical Error")
    st.write(e)

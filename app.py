import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Sales Tracker", layout="centered")

# --- 2. PASSWORD PROTECTION LOGIC ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔒 Access Required")
    pwd_input = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if pwd_input == "zsigns2030":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect password.")
    return False

if not check_password():
    st.stop()

# --- 3. MAIN APP CONTENT ---
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = st.secrets["gsheet_url"]

def load_data():
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
    data.columns = [str(c).strip() for c in data.columns]
    return data

st.title("📦 Sales Recorder")

try:
    df = load_data()

    if df.empty or len(df) == 0:
        st.warning("📋 Your Inventory sheet is empty.")
    else:
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
            stock = int(pd.to_numeric(str(row['Quantity (PC)']).replace(',', ''), errors='coerce') or 0)
            base_price = float(pd.to_numeric(str(row['TZS']).replace(',', ''), errors='coerce') or 0)
            
            st.divider()
            col_a, col_b = st.columns(2)
            col_a.metric(label="In Stock", value=f"{stock} PC")
            col_b.metric(label="Base Price", value=f"{base_price:,.0f} TZS")

            st.subheader("4. Record Sale Details")
            col1, col2 = st.columns(2)
            qty_sold = col1.number_input("Quantity Sold", min_value=1, max_value=max(1, stock), value=1)
            actual_price = col2.number_input("Actual Selling Price (per PC)", value=base_price, step=500.0)
            
            total_sale = qty_sold * actual_price
            st.info(f"💰 **Total Sale Amount: {total_sale:,.0f} TZS**")
            
            if st.button("Confirm Sale & Sync ✅", use_container_width=True):
                # Update Inventory
                idx = match.index[0]
                df.at[idx, 'Quantity (PC)'] = stock - qty_sold
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)
                
                # Log to Sales
                try:
                    sales_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sales", ttl=0)
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Item": selected_desc,
                        "Color": selected_color,
                        "Thickness": selected_thick,
                        "Qty Sold": qty_sold,
                        "Price Each": actual_price,
                        "Total Amount": total_sale,
                        "Stock Left": stock - qty_sold
                    }])
                    updated_sales = pd.concat([sales_df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sales", data=updated_sales)
                    st.success("Success!")
                    st.rerun()
                except Exception as sales_err:
                    st.error(f"Inventory updated, but Sales log failed: {sales_err}")

except Exception as e:
    st.error(f"Setup Error: {e}")

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- FILE NAMES ---
# Change this to match the filename you uploaded to GitHub exactly
INV_FILE = "inventory.csv" 
SALES_FILE = "sales_log.csv"

st.set_page_config(page_title="Sales Tracker", layout="centered")

# --- DATA LOADING ---
def load_data():
    if os.path.exists(INV_FILE):
        return pd.read_csv(INV_FILE)
    else:
        st.error(f"File {INV_FILE} not found! Please upload it to GitHub.")
        return pd.DataFrame()

df_inv = load_data()

# --- APP UI ---
st.title("🛒 Sales Recording System")

if not df_inv.empty:
    with st.form("sale_form", clear_on_submit=True):
        # 1. Select Item (Description)
        item_choice = st.selectbox("Select Item", df_inv['Description'].unique())
        
        # 2. Filter for Color/Finish
        filtered_colors = df_inv[df_inv['Description'] == item_choice]
        color_choice = st.selectbox("Color/Finish", filtered_colors['Color/Finish'].unique())
        
        # 3. Filter for Thickness
        filtered_thickness = filtered_colors[filtered_colors['Color/Finish'] == color_choice]
        thick_choice = st.selectbox("Thickness", filtered_thickness['Thickness'].unique())
        
        # Get the specific row to check stock
        target_row = filtered_thickness[filtered_thickness['Thickness'] == thick_choice].iloc[0]
        max_stock = int(target_row['Quantity (PC)'])
        size_info = target_row['Size (mm)']
        default_price = float(target_row['TZS'])

        st.info(f"Size: {size_info} | Current Stock: {max_stock} units")

        # 4. Inputs
        col1, col2 = st.columns(2)
        qty = col1.number_input("Quantity Sold", min_value=1, max_value=max_stock if max_stock > 0 else 1)
        price = col2.number_input("Price (TZS)", min_value=0.0, value=default_price)
        
        submitted = st.form_submit_button("Confirm Sale")

    if submitted:
        if max_stock >= qty:
            # Calculate remaining
            remaining = max_stock - qty
            
            # Update the inventory dataframe
            idx = df_inv[(df_inv['Description'] == item_choice) & 
                        (df_inv['Color/Finish'] == color_choice) & 
                        (df_inv['Thickness'] == thick_choice)].index
            df_inv.at[idx[0], 'Quantity (PC)'] = remaining
            
            # Save updated inventory back to CSV
            df_inv.to_csv(INV_FILE, index=False)
            
            # Record sale in sales_log.csv
            new_sale = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Item": item_choice,
                "Color": color_choice,
                "Thickness": thick_choice,
                "Qty Sold": qty,
                "Total Price": price * qty,
                "Stock Left": remaining
            }
            
            # Append sale to log
            if os.path.exists(SALES_FILE):
                sales_df = pd.read_csv(SALES_FILE)
                sales_df = pd.concat([sales_df, pd.DataFrame([new_sale])], ignore_index=True)
            else:
                sales_df = pd.DataFrame([new_sale])
            
            sales_df.to_csv(SALES_FILE, index=False)
            
            st.success(f"Sale Recorded! {remaining} left in stock.")
            st.rerun()
        else:
            st.error("Error: Not enough stock available!")

st.divider()
st.subheader("Inventory Preview")
st.dataframe(df_inv)

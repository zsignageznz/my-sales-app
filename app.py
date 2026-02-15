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
        
        # CLEANING DATA: Remove accidental spaces from names/categories
        for col in ['Description', 'Color/Finish', 'Thickness']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Clean the TZS price column
        if 'TZS' in df.columns:
            df['TZS'] = df['TZS'].astype(str).str.replace(',', '').str.strip().astype(float)
        
        return df
    return pd.DataFrame()

st.title("📦 Sales Recorder")

df = load_data()

if df.empty:
    st.error(f"File {INV_FILE} not found. Please upload it to GitHub.")
else:
    # We use a form to group the inputs
    with st.form("sale_form"):
        # 1. Select Description
        all_descriptions = sorted(df['Description'].unique())
        desc = st.selectbox("1. Select Item Description", all_descriptions)
        
        # 2. Filter data for the chosen Description
        sub_df = df[df['Description'] == desc]
        
        # 3. Select Color/Finish based on that Item
        available_colors = sorted(sub_df['Color/Finish'].unique())
        color_choice = st.selectbox("2. Select Color/Finish", available_colors)
        
        # 4. Filter further for Thickness
        color_df = sub_df[sub_df['Color/Finish'] == color_choice]
        available_thickness = sorted(color_df['Thickness'].unique())
        thick_choice = st.selectbox("3. Select Thickness", available_thickness)
        
        # 5. Get the final specific row for Size, Stock, and Price
        final_match = color_df[color_df['Thickness'] == thick_choice]
        
        if not final_match.empty:
            row = final_match.iloc[0]
            current_stock = int(row['Quantity (PC)'])
            item_size = row['Size (mm)']
            item_price = float(row['TZS'])

            # Displaying the live info for the selected specific item
            st.info(f"📏 Size: {item_size} | 📈 Stock: {current_stock} | 💰 Price: {item_price:,.0f} TZS")
            
            # User Inputs
            qty = st.number_input("Quantity to Sell", min_value=1, max_value=max(1, current_stock))
            price_sold = st.number_input("Confirmed Price (Per PC)", value=item_price)
            
            submit = st.form_submit_button("Confirm Sale ✅")
        else:
            st.error("Selection error. Please check your inventory file.")
            submit = False

    if submit:
        if current_stock >= qty:
            # Update the original dataframe
            idx = final_match.index[0]
            df.at[idx, 'Quantity (PC)'] -= qty
            
            # Save updated inventory back to CSV
            df.to_csv(INV_FILE, index=False)
            
            # Save the sale to the log
            log_entry = pd.DataFrame([{
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Item": desc, 
                "Finish": color_choice,
                "Thickness": thick_choice,
                "Qty": qty, 
                "Price": price_sold,
                "Total": price_sold * qty
            }])
            
            if os.path.exists(SALES_FILE):
                log_entry.to_csv(SALES_FILE, mode='a', header=False, index=False)
            else:
                log_entry.to_csv(SALES_FILE, index=False)
                
            st.success("Sale Saved! Stock updated.")
            st.rerun()
        else:
            st.error("Not enough stock for this sale!")

st.divider()
st.subheader("Current Inventory Status")
st.dataframe(df, use_container_width=True)

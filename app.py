{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh11820\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import os\
from datetime import datetime\
\
# File to store data permanently\
DATA_FILE = "sales_data.csv"\
\
# Load data or create if it doesn't exist\
if os.path.exists(DATA_FILE):\
    df_sales = pd.read_csv(DATA_FILE)\
else:\
    df_sales = pd.DataFrame(columns=['Item', 'Description', 'Qty', 'Price', 'Timestamp'])\
\
# ... (The rest of your UI code goes here)\
\
# When saving:\
# df_sales.to_csv(DATA_FILE, index=False)\
\
# 1. Setup Initial Data (In a real app, this would load from a CSV/Database)\
if 'inventory' not in st.session_state:\
    st.session_state.inventory = pd.DataFrame(\{\
        'Item': ['Laptop', 'Mouse', 'Keyboard'],\
        'Description': ['15-inch Gaming', 'Wireless Optical', 'Mechanical RGB'],\
        'Stock': [10, 50, 25]\
    \})\
\
if 'sales_log' not in st.session_state:\
    st.session_state.sales_log = pd.DataFrame(columns=['Item', 'Description', 'Quantity Sold', 'Price', 'Timestamp'])\
\
st.title("\uc0\u55357 \u56960  Simple Sales Recorder")\
\
# 2. User Input Section\
st.subheader("Record a Sale")\
with st.form("sale_form"):\
    # Dropdown to select item\
    selected_item = st.selectbox("Select Item", st.session_state.inventory['Item'])\
    \
    # Auto-fill description based on selection\
    item_details = st.session_state.inventory[st.session_state.inventory['Item'] == selected_item].iloc[0]\
    st.write(f"**Description:** \{item_details['Description']\}")\
    \
    # Inputs\
    qty_sold = st.number_input("Quantity Sold", min_value=1, max_value=int(item_details['Stock']), step=1)\
    price = st.number_input("Selling Price ($)", min_value=0.0, step=0.01, value=0.0)\
    \
    submit = st.form_submit_button("Record Sale")\
\
# 3. Logic to Update Stock\
if submit:\
    # Update Inventory\
    st.session_state.inventory.loc[st.session_state.inventory['Item'] == selected_item, 'Stock'] -= qty_sold\
    \
    # Log the Sale\
    new_sale = \{\
        'Item': selected_item,\
        'Description': item_details['Description'],\
        'Quantity Sold': qty_sold,\
        'Price': price,\
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")\
    \}\
    st.session_state.sales_log = pd.concat([st.session_state.sales_log, pd.DataFrame([new_sale])], ignore_index=True)\
    st.success(f"Sold \{qty_sold\} \{selected_item\}(s) successfully!")\
\
---\
\
### 4. Dashboard Views\
col1, col2 = st.columns(2)\
\
with col1:\
    st.subheader("Current Inventory")\
    st.dataframe(st.session_state.inventory, use_container_width=True)\
\
with col2:\
    st.subheader("Sales History")\
    st.dataframe(st.session_state.sales_log, use_container_width=True)}

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from reagent_optimizer import ReagentOptimizer
import sqlite3
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Reagent Tray LIMS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for attractive formatting
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F2F6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .reportview-container .main .block-container {
        padding-top: 1rem;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Database setup
conn = sqlite3.connect('reagent_tray_lims.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS work_orders
             (id INTEGER PRIMARY KEY, customer TEXT, date TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS trays
             (id INTEGER PRIMARY KEY, wo_id INTEGER, customer TEXT, date TEXT, configuration TEXT)''')
conn.commit()

# Main function
def main():
    st.title("🧪 Reagent Tray LIMS")

    tabs = st.tabs(["Dashboard", "Work Orders", "Tray Configuration", "Inventory", "Production & QC", "Shipping & Logging"])

    with tabs[0]:
        show_dashboard()
    with tabs[1]:
        show_work_orders()
    with tabs[2]:
        show_tray_configuration()
    with tabs[3]:
        show_inventory()
    with tabs[4]:
        show_production_and_qc()
    with tabs[5]:
        show_shipping_and_logging()

def show_dashboard():
    st.header("Dashboard")
    
    # Fetch real data from the database
    c.execute("SELECT COUNT(*) FROM work_orders WHERE status='Open'")
    open_wo = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM trays WHERE date=?", (datetime.now().strftime('%Y-%m-%d'),))
    trays_today = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM trays WHERE date>=date('now', '-7 days')")
    trays_this_week = c.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Open Work Orders", value=open_wo)
    with col2:
        st.metric(label="Trays Created Today", value=trays_today)
    with col3:
        st.metric(label="Trays Created This Week", value=trays_this_week)

    # Fetch data for charts
    c.execute("SELECT date, COUNT(*) FROM work_orders GROUP BY date ORDER BY date")
    wo_data = c.fetchall()
    c.execute("SELECT date, COUNT(*) FROM trays GROUP BY date ORDER BY date")
    tray_data = c.fetchall()

    if wo_data and tray_data:
        wo_df = pd.DataFrame(wo_data, columns=['date', 'count'])
        tray_df = pd.DataFrame(tray_data, columns=['date', 'count'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=wo_df['date'], y=wo_df['count'], mode='lines', name='Work Orders'))
        fig.add_trace(go.Scatter(x=tray_df['date'], y=tray_df['count'], mode='lines', name='Trays Created'))
        fig.update_layout(title='Work Orders and Trays Over Time', xaxis_title='Date', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to display charts yet.")

def show_work_orders():
    st.header("Work Order Management")
    
    # Form for new work orders
    with st.form("new_work_order"):
        customer = st.text_input("Customer Name")
        date = st.date_input("Order Date")
        submitted = st.form_submit_button("Create Work Order")
        if submitted:
            c.execute("INSERT INTO work_orders (customer, date, status) VALUES (?, ?, ?)",
                      (customer, date.strftime('%Y-%m-%d'), 'Open'))
            conn.commit()
            st.success(f"Work Order created for {customer} on {date}")

    # Display existing work orders
    c.execute("SELECT * FROM work_orders ORDER BY date DESC")
    work_orders = c.fetchall()
    if work_orders:
        df = pd.DataFrame(work_orders, columns=['ID', 'Customer', 'Date', 'Status'])
        st.dataframe(df)
    else:
        st.info("No work orders found. Create a new work order to get started.")

def show_tray_configuration():
    st.header("Tray Configuration")
    
    # Select work order
    c.execute("SELECT id, customer, date FROM work_orders WHERE status='Open'")
    open_work_orders = c.fetchall()
    if not open_work_orders:
        st.warning("No open work orders. Please create a work order first.")
        return

    selected_wo = st.selectbox("Select Work Order", 
                               options=open_work_orders,
                               format_func=lambda x: f"{x[1]} - {x[2]}")

    optimizer = ReagentOptimizer()
    experiments = optimizer.get_available_experiments()

    selected_experiments = st.multiselect("Select experiments", 
                                          options=[f"{exp['id']}: {exp['name']}" for exp in experiments])
    selected_ids = [int(exp.split(':')[0]) for exp in selected_experiments]

    if st.button("Optimize Configuration"):
        if not selected_ids:
            st.error("Please select at least one experiment")
        else:
            try:
                with st.spinner("Optimizing tray configuration..."):
                    config = optimizer.optimize_tray_configuration(selected_ids)
                
                # Save tray configuration
                c.execute("INSERT INTO trays (wo_id, customer, date, configuration) VALUES (?, ?, ?, ?)",
                          (selected_wo[0], selected_wo[1], datetime.now().strftime('%Y-%m-%d'), str(config)))
                conn.commit()
                
                st.session_state.config = config
                st.success("Configuration optimized and saved successfully!")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    if 'config' in st.session_state:
        display_results(st.session_state.config)

def display_results(config):
    st.subheader("Tray Configuration")
    fig = create_tray_visualization(config)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Results Summary")
    tray_life = min(result["total_tests"] for result in config["results"].values())
    st.metric("Tray Life (Tests)", tray_life)

    results_df = pd.DataFrame([
        {
            "Experiment": f"{result['name']} (#{exp_num})",
            "Total Tests": result['total_tests']
        }
        for exp_num, result in config["results"].items()
    ])
    st.dataframe(results_df)

def create_tray_visualization(config):
    # (The create_tray_visualization function remains unchanged)
    # ... (Keep the existing implementation)

def get_reagent_color(reagent_code):
    # (The get_reagent_color function remains unchanged)
    # ... (Keep the existing implementation)

def show_inventory():
    st.header("Inventory Management")
    
    # Form for adding new inventory items
    with st.form("new_inventory"):
        reagent = st.text_input("Reagent")
        batch_number = st.text_input("Batch Number")
        quantity = st.number_input("Quantity", min_value=0)
        submitted = st.form_submit_button("Add Item")
        if submitted:
            # In a real application, you would save this to the database
            st.success(f"Added {quantity} of {reagent} (Batch: {batch_number}) to inventory")

    # In a real application, you would fetch this data from the database
    st.info("Inventory data would be displayed here. Implement database integration for real data.")

def show_production_and_qc():
    st.header("Production & QC")
    
    # Select tray for production
    c.execute("SELECT id, customer, date FROM trays WHERE id NOT IN (SELECT tray_id FROM production)")
    trays_for_production = c.fetchall()
    if not trays_for_production:
        st.warning("No trays available for production. Please configure a tray first.")
        return

    selected_tray = st.selectbox("Select Tray for Production", 
                                 options=trays_for_production,
                                 format_func=lambda x: f"{x[1]} - {x[2]}")

    # Production steps
    st.subheader("Production Steps")
    steps = ["Pour reagents", "Seal tray", "Apply label", "Package"]
    completed_steps = []
    for step in steps:
        if st.checkbox(step):
            completed_steps.append(step)

    # QC checklist
    st.subheader("QC Checklist")
    qc_items = ["Volume check", "Seal integrity", "Label accuracy", "Packaging quality"]
    completed_qc = []
    for item in qc_items:
        if st.checkbox(item):
            completed_qc.append(item)

    if st.button("Complete Production & QC"):
        if len(completed_steps) == len(steps) and len(completed_qc) == len(qc_items):
            # In a real application, you would save this information to the database
            st.success("Production and QC completed successfully!")
        else:
            st.warning("Please complete all production steps and QC checks before proceeding.")

def show_shipping_and_logging():
    st.header("Shipping & Logging")
    
    # Select tray for shipping
    c.execute("SELECT id, customer, date FROM trays WHERE id NOT IN (SELECT tray_id FROM shipping)")
    trays_for_shipping = c.fetchall()
    if not trays_for_shipping:
        st.warning("No trays available for shipping. Please complete production and QC first.")
        return

    selected_tray = st.selectbox("Select Tray for Shipping", 
                                 options=trays_for_shipping,
                                 format_func=lambda x: f"{x[1]} - {x[2]}")

    # Form for logging new shipments
    with st.form("new_shipment"):
        tracking_number = st.text_input("Tracking Number")
        ship_date = st.date_input("Ship Date")
        submitted = st.form_submit_button("Log Shipment")
        if submitted:
            # In a real application, you would save this to the database
            st.success(f"Shipment logged for {selected_tray[1]} with tracking number {tracking_number}")

    # In a real application, you would fetch this data from the database
    st.info("Shipment log would be displayed here. Implement database integration for real data.")

if __name__ == "__main__":
    main()


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
    .stTabs {
        background-color: #f0f2f6;
        padding: 10px 0px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
        gap: 1px;
        padding: 10px 16px;
        margin: 0px 2px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #45a049;
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
    .workflow-progress {
        margin-bottom: 20px;
    }
    .workflow-progress .stProgress > div > div {
        background-color: #4CAF50;
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
c.execute('''CREATE TABLE IF NOT EXISTS production
             (id INTEGER PRIMARY KEY, tray_id INTEGER, start_date TEXT, end_date TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS shipping
             (id INTEGER PRIMARY KEY, tray_id INTEGER, tracking_number TEXT, ship_date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS inventory
             (id INTEGER PRIMARY KEY, reagent TEXT, batch_number TEXT, quantity INTEGER, date_added TEXT)''')
conn.commit()

def get_workflow_progress():
    c.execute("SELECT COUNT(*) FROM work_orders WHERE status='Open'")
    open_orders = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM production WHERE status='In Progress'")
    in_progress = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM production WHERE status='Completed'")
    completed = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM shipping")
    shipped = c.fetchone()[0]
    
    total = open_orders + in_progress + completed + shipped
    if total == 0:
        return 0
    
    if shipped > 0:
        return 100
    elif completed > 0:
        return 75
    elif in_progress > 0:
        return 50
    elif open_orders > 0:
        return 25
    else:
        return 0

# Main function
def main():
    st.title("🧪 Reagent Tray LIMS")

    # Add workflow progress bar
    progress = get_workflow_progress()
    st.progress(progress / 100, "Workflow Progress")
    st.write(f"Current Stage: {'Shipped' if progress == 100 else 'Packing' if progress >= 75 else 'In Progress' if progress >= 50 else 'Open' if progress >= 25 else 'No Active Orders'}")

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
    locations = config["tray_locations"]
    fig = go.Figure()

    for i, loc in enumerate(locations):
        row = i // 4
        col = i % 4
        color = get_reagent_color(loc['reagent_code']) if loc else 'lightgray'
        opacity = 0.8 if loc else 0.2

        fig.add_trace(go.Scatter(
            x=[col, col+1, col+1, col, col],
            y=[row, row, row+1, row+1, row],
            fill="toself",
            fillcolor=color,
            opacity=opacity,
            line=dict(color="black", width=1),
            mode="lines",
            name=f"LOC-{i+1}",
            text=f"LOC-{i+1}<br>{loc['reagent_code'] if loc else 'Empty'}<br>Tests: {loc['tests_possible'] if loc else 'N/A'}<br>Exp: #{loc['experiment'] if loc else 'N/A'}",
            hoverinfo="text"
        ))

        fig.add_annotation(
            x=(col + col + 1) / 2,
            y=(row + row + 1) / 2,
            text=f"LOC-{i+1}<br>{loc['reagent_code'] if loc else 'Empty'}<br>Tests: {loc['tests_possible'] if loc else 'N/A'}<br>Exp: #{loc['experiment'] if loc else 'N/A'}",
            showarrow=False,
            font=dict(color="black", size=8),
            align="center",
            xanchor="center",
            yanchor="middle"
        )

    fig.update_layout(
        title="Tray Configuration",
        showlegend=False,
        height=600,
        width=800,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

def get_reagent_color(reagent_code):
    color_map = {
        'gray': ['KR1E', 'KR1S', 'KR2S', 'KR3E', 'KR3S', 'KR4E', 'KR4S', 'KR5E', 'KR5S', 'KR6E1', 'KR6E2', 'KR6E3', 'KR13E1', 'KR13S', 'KR14E', 'KR14S', 'KR15E', 'KR15S'],
        'violet': ['KR7E1', 'KR7E2', 'KR8E1', 'KR8E2', 'KR19E1', 'KR19E2', 'KR19E3', 'KR20E', 'KR36E1', 'KR36E2', 'KR40E1', 'KR40E2'],
        'green': ['KR9E1', 'KR9E2', 'KR17E1', 'KR17E2', 'KR17E3', 'KR28E1', 'KR28E2', 'KR28E3'],
        'orange': ['KR10E1', 'KR10E2', 'KR10E3', 'KR12E1', 'KR12E2', 'KR12E3', 'KR18E1', 'KR18E2', 'KR22E1', 'KR27E1', 'KR27E2', 'KR42E1', 'KR42E2'],
        'white': ['KR11E', 'KR21E1'],
        'blue': ['KR16E1', 'KR16E2', 'KR16E3', 'KR16E4', 'KR30E1', 'KR30E2', 'KR30E3', 'KR31E1', 'KR31E2', 'KR34E1', 'KR34E2'],
        'red': ['KR29E1', 'KR29E2', 'KR29E3'],
        'yellow': ['KR35E1', 'KR35E2']
    }
    for color, reagents in color_map.items():
        if any(reagent_code.startswith(r) for r in reagents):
            return color
    return 'lightgray'  # Default color if not found



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
    c.execute("""
        SELECT t.id, t.customer, t.date 
        FROM trays t
        LEFT JOIN production p ON t.id = p.tray_id
        WHERE p.tray_id IS NULL
    """)
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
            # Save production information to the database
            c.execute("""
                INSERT INTO production (tray_id, start_date, end_date, status)
                VALUES (?, ?, ?, ?)
            """, (selected_tray[0], datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'), 'Completed'))
            conn.commit()
            st.success("Production and QC completed successfully!")
        else:
            st.warning("Please complete all production steps and QC checks before proceeding.")

def show_shipping_and_logging():
    st.header("Shipping & Logging")
    
    # Select tray for shipping
    c.execute("""
        SELECT t.id, t.customer, t.date 
        FROM trays t
        INNER JOIN production p ON t.id = p.tray_id
        LEFT JOIN shipping s ON t.id = s.tray_id
        WHERE p.status = 'Completed' AND s.tray_id IS NULL
    """)
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
            # Save shipping information to the database
            c.execute("""
                INSERT INTO shipping (tray_id, tracking_number, ship_date)
                VALUES (?, ?, ?)
            """, (selected_tray[0], tracking_number, ship_date.strftime('%Y-%m-%d')))
            conn.commit()
            st.success(f"Shipment logged for {selected_tray[1]} with tracking number {tracking_number}")

    # Display shipping log
    c.execute("""
        SELECT t.customer, s.tracking_number, s.ship_date
        FROM shipping s
        INNER JOIN trays t ON s.tray_id = t.id
        ORDER BY s.ship_date DESC
    """)
    shipping_log = c.fetchall()
    
    if shipping_log:
        st.subheader("Shipping Log")
        df = pd.DataFrame(shipping_log, columns=['Customer', 'Tracking Number', 'Ship Date'])
        st.dataframe(df)
    else:
        st.info("No shipments logged yet.")

if __name__ == "__main__":
    main()


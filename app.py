import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import uuid
from reagent_optimizer import ReagentOptimizer

# Initialize session state
if 'requests' not in st.session_state:
    st.session_state.requests = []
if 'inventory' not in st.session_state:
    st.session_state.inventory = []
if 'tray_configurations' not in st.session_state:
    st.session_state.tray_configurations = []
if 'production_records' not in st.session_state:
    st.session_state.production_records = []
if 'shipments' not in st.session_state:
    st.session_state.shipments = []

# Utility functions
def generate_id():
    return str(uuid.uuid4())

def get_reagent_color(reagent_code):
    color_map = {
        'gray': ['KR1E', 'KR1S', 'KR2S', 'KR3E', 'KR3S'],
        'violet': ['KR7E1', 'KR7E2', 'KR8E1', 'KR8E2'],
        'green': ['KR9E1', 'KR9E2', 'KR17E1', 'KR17E2'],
        'orange': ['KR10E1', 'KR10E2', 'KR10E3'],
        'blue': ['KR16E1', 'KR16E2', 'KR16E3', 'KR16E4'],
        'red': ['KR29E1', 'KR29E2', 'KR29E3'],
        'yellow': ['KR35E1', 'KR35E2']
    }
    for color, reagents in color_map.items():
        if any(reagent_code.startswith(r) for r in reagents):
            return color
    return 'lightgray'  # Default color if not found

# Request Management
def request_management():
    st.header("Request Management")
    
    # Add new request
    with st.form("new_request"):
        customer = st.text_input("Customer Name")
        date = st.date_input("Request Date")
        if st.form_submit_button("Add Request"):
            new_request = {
                "id": generate_id(),
                "customer": customer,
                "date": date.strftime("%Y-%m-%d"),
                "status": "Pending"
            }
            st.session_state.requests.append(new_request)
            st.success("Request added successfully!")

    # Display requests
    if st.session_state.requests:
        df = pd.DataFrame(st.session_state.requests)
        st.dataframe(df)
    else:
        st.info("No requests yet.")

# Tray Configuration
def tray_configuration():
    st.header("Tray Configuration")
    
    # Select a request to configure
    request_ids = [r['id'] for r in st.session_state.requests if r['status'] == 'Pending']
    selected_request = st.selectbox("Select Request to Configure", request_ids)
    
    if selected_request:
        reagents = ['KR1E', 'KR1S', 'KR2S', 'KR3E', 'KR3S', 'KR10E1', 'KR10E2', 'KR10E3']
        tray_config = [None] * 16
        
        st.subheader("Configure Tray")
        cols = st.columns(4)
        for i in range(16):
            with cols[i % 4]:
                tray_config[i] = st.selectbox(f"Chamber {i+1}", [''] + reagents, key=f"chamber_{i}")
        
        if st.button("Save Configuration"):
            new_config = {
                "id": generate_id(),
                "request_id": selected_request,
                "configuration": tray_config,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.tray_configurations.append(new_config)
            st.success("Tray configuration saved!")

        # Visualize tray configuration
        if any(tray_config):
            fig = go.Figure()
            for i, reagent in enumerate(tray_config):
                row = i // 4
                col = i % 4
                color = get_reagent_color(reagent) if reagent else 'lightgray'
                opacity = 0.8 if reagent else 0.2

                fig.add_trace(go.Scatter(
                    x=[col, col+1, col+1, col, col],
                    y=[row, row, row+1, row+1, row],
                    fill="toself",
                    fillcolor=color,
                    opacity=opacity,
                    line=dict(color="black", width=1),
                    mode="lines",
                    name=f"Chamber {i+1}",
                    text=f"Chamber {i+1}<br>{reagent if reagent else 'Empty'}",
                    hoverinfo="text"
                ))

            fig.update_layout(
                title="Tray Configuration",
                showlegend=False,
                height=400,
                width=600,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig)

# Inventory Management
def inventory_management():
    st.header("Inventory Management")
    
    # Add new inventory item
    with st.form("new_inventory"):
        reagent = st.text_input("Reagent")
        batch_number = st.text_input("Batch Number")
        quantity = st.number_input("Quantity", min_value=0)
        if st.form_submit_button("Add Inventory Item"):
            new_item = {
                "id": generate_id(),
                "reagent": reagent,
                "batch_number": batch_number,
                "quantity": quantity
            }
            st.session_state.inventory.append(new_item)
            st.success("Inventory item added successfully!")

    # Display inventory
    if st.session_state.inventory:
        df = pd.DataFrame(st.session_state.inventory)
        st.dataframe(df)
    else:
        st.info("No inventory items yet.")

# Production and QC
def production_and_qc():
    st.header("Production and QC")
    
    # Select a tray configuration to produce
    config_ids = [c['id'] for c in st.session_state.tray_configurations]
    selected_config = st.selectbox("Select Tray Configuration", config_ids)
    
    if selected_config:
        production_steps = [
            "Pour reagents into tray",
            "Seal tray chambers",
            "Apply tray label",
            "Package tray in box"
        ]
        qc_checklist = [
            "Verify reagent volumes",
            "Check tray seal integrity",
            "Confirm label accuracy",
            "Inspect packaging"
        ]
        
        st.subheader("Production Steps")
        completed_steps = []
        for step in production_steps:
            if st.checkbox(step, key=f"prod_{step}"):
                completed_steps.append(step)
        
        st.subheader("QC Checklist")
        completed_qc = []
        for item in qc_checklist:
            if st.checkbox(item, key=f"qc_{item}"):
                completed_qc.append(item)
        
        if st.button("Complete Production & QC"):
            new_record = {
                "id": generate_id(),
                "config_id": selected_config,
                "completed_steps": completed_steps,
                "completed_qc": completed_qc,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.production_records.append(new_record)
            st.success("Production and QC record saved!")

# Shipping and Logging
def shipping_and_logging():
    st.header("Shipping and Logging")
    
    # Add new shipment
    with st.form("new_shipment"):
        config_ids = [c['id'] for c in st.session_state.tray_configurations]
        selected_config = st.selectbox("Select Tray Configuration", config_ids)
        tracking_number = st.text_input("Tracking Number")
        date = st.date_input("Shipping Date")
        if st.form_submit_button("Log Shipment"):
            new_shipment = {
                "id": generate_id(),
                "config_id": selected_config,
                "tracking_number": tracking_number,
                "date": date.strftime("%Y-%m-%d")
            }
            st.session_state.shipments.append(new_shipment)
            st.success("Shipment logged successfully!")

    # Display shipments
    if st.session_state.shipments:
        df = pd.DataFrame(st.session_state.shipments)
        st.dataframe(df)
    else:
        st.info("No shipments logged yet.")

# Main app
def main():
    st.set_page_config(page_title="Reagent Tray LIMS", page_icon="🧪", layout="wide")
    st.title("🧪 Reagent Tray LIMS")

    # Sidebar navigation
    page = st.sidebar.radio("Navigate", ["Requests", "Tray Configuration", "Inventory", "Production & QC", "Shipping & Logging"])

    if page == "Requests":
        request_management()
    elif page == "Tray Configuration":
        tray_configuration()
    elif page == "Inventory":
        inventory_management()
    elif page == "Production & QC":
        production_and_qc()
    elif page == "Shipping & Logging":
        shipping_and_logging()

if __name__ == "__main__":
    main()

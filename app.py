import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import uuid
import base64
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import slack

# Import the ReagentOptimizer
from reagent_optimizer import ReagentOptimizer

# Set page config
st.set_page_config(page_title="Reagent Tray LIMS", page_icon="🧪", layout="wide")


# Utility functions
def generate_id():
    return str(uuid.uuid4())

# Define all your functions here
def dashboard():
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)

    jobs_df = pd.DataFrame(st.session_state.jobs)

    with col1:
        st.metric("Total Jobs", len(jobs_df))

    with col2:
        open_jobs = len(jobs_df[jobs_df['status'] == 'Open']) if 'status' in jobs_df.columns else 0
        st.metric("Open Jobs", open_jobs)

    with col3:
        closed_jobs = len(jobs_df[jobs_df['status'] == 'Closed']) if 'status' in jobs_df.columns else 0
        st.metric("Closed Jobs", closed_jobs)

    # Job Status Chart
    if 'status' in jobs_df.columns:
        status_counts = jobs_df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig = px.pie(status_counts, values='count', names='status', title='Job Status Distribution')
        st.plotly_chart(fig)
    else:
        st.warning("Job status information is not available.")

    # Recent Jobs
    st.subheader("Recent Jobs")
    if not jobs_df.empty:
        if 'date' in jobs_df.columns:
            jobs_df['date'] = pd.to_datetime(jobs_df['date'])
            recent_jobs = jobs_df.sort_values('date', ascending=False).head(5)
            st.dataframe(recent_jobs)
        else:
            st.dataframe(jobs_df.head(5))
    else:
        st.info("No recent jobs.")

def job_management():
    st.header("Job Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("new_job"):
            customer = st.text_input("Customer Name")
            analyst = st.text_input("Analyst Name")
            date = st.date_input("Request Date")
            status = st.selectbox("Status", options=["Open", "Closed"])
            if st.form_submit_button("Create New Job"):
                new_job = {
                    "id": generate_id(),
                    "customer": customer,
                    "analyst": analyst,
                    "date": date.isoformat(),
                    "status": status,
                    "tray_configuration": None,
                    "production_record": None,
                    "shipment_info": None
                }
                st.session_state.jobs.append(new_job)
                st.success("New job created successfully!")

    with col2:
        if st.session_state.jobs:
            df = pd.DataFrame(st.session_state.jobs)
            st.dataframe(df)
        else:
            st.info("No jobs yet.")

def tray_configuration():
    st.header("Tray Configuration")
    # Implement tray configuration logic here

def inventory_management():
    st.header("Inventory Management")
    # Implement inventory management logic here

def production_and_qc():
    st.header("Production and QC")
    # Implement production and QC logic here

def shipping_and_logging():
    st.header("Shipping and Logging")
    # Implement shipping and logging logic here

def equipment_integration():
    st.header("Equipment Integration")
    # Implement equipment integration logic here

def analytics():
    st.header("Analytics")
    # Implement analytics logic here

# Main function
def main():
    st.title("🧪 Reagent Tray LIMS")

    # Initialize session state
    if 'jobs' not in st.session_state:
        st.session_state.jobs = []

    # Horizontal top menu using tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Dashboard", "Job Management", "Tray Configuration", "Inventory", 
        "Production & QC", "Shipping & Logging", "Equipment", "Analytics"
    ])

    with tab1:
        dashboard()

    with tab2:
        job_management()

    with tab3:
        tray_configuration()

    with tab4:
        inventory_management()

    with tab5:
        production_and_qc()

    with tab6:
        shipping_and_logging()

    with tab7:
        equipment_integration()

    with tab8:
        analytics()


def dashboard():
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)

    jobs_df = pd.DataFrame(st.session_state.jobs)

    with col1:
        st.metric("Total Jobs", len(jobs_df))

    with col2:
        open_jobs = len(jobs_df[jobs_df['status'] == 'Open']) if 'status' in jobs_df.columns else 0
        st.metric("Open Jobs", open_jobs)

    with col3:
        closed_jobs = len(jobs_df[jobs_df['status'] == 'Closed']) if 'status' in jobs_df.columns else 0
        st.metric("Closed Jobs", closed_jobs)

    # Job Status Chart
    if 'status' in jobs_df.columns:
        status_counts = jobs_df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig = px.pie(status_counts, values='count', names='status', title='Job Status Distribution')
        st.plotly_chart(fig)
    else:
        st.warning("Job status information is not available.")

    # Recent Jobs
    st.subheader("Recent Jobs")
    if not jobs_df.empty:
        if 'date' in jobs_df.columns:
            jobs_df['date'] = pd.to_datetime(jobs_df['date'])
            recent_jobs = jobs_df.sort_values('date', ascending=False).head(5)
            st.dataframe(recent_jobs)
        else:
            st.dataframe(jobs_df.head(5))
    else:
        st.info("No recent jobs.")

    # Add more visualizations or metrics as needed

def job_management():
    st.header("Job Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("new_job"):
            customer = st.text_input("Customer Name")
            analyst = st.text_input("Analyst Name")
            date = st.date_input("Request Date")
            status = st.selectbox("Status", options=["Open", "Closed"])
            if st.form_submit_button("Create New Job"):
                new_job = {
                    "id": generate_id(),
                    "customer": customer,
                    "analyst": analyst,
                    "date": date.isoformat(),
                    "status": status,
                    "tray_configuration": None,
                    "production_record": None,
                    "shipment_info": None
                }
                st.session_state.jobs.append(new_job)
                st.success("New job created successfully!")

    with col2:
        if st.session_state.jobs:
            df = pd.DataFrame(st.session_state.jobs)
            st.dataframe(df)
        else:
            st.info("No jobs yet.")

def tray_configuration():
    st.header("Tray Configuration")
    
    job_id = st.selectbox("Select Job", options=[job['id'] for job in st.session_state.jobs if job['status'] == 'Open'])
    
    if job_id:
        job_index = next(i for i, job in enumerate(st.session_state.jobs) if job['id'] == job_id)
        job = st.session_state.jobs[job_index]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Simulating tray configuration
            st.subheader("Configure Tray")
            reagents = ['KR1E', 'KR1S', 'KR2S', 'KR3E', 'KR3S', 'KR10E1', 'KR10E2', 'KR10E3']
            selected_reagents = []
            for i in range(16):
                selected_reagents.append(st.selectbox(f"Chamber {i+1}", options=[''] + reagents, key=f"chamber_{i}"))
            
            if st.button("Save Configuration"):
                tray_config = {
                    "tray_locations": [{"reagent_code": r, "location": i} for i, r in enumerate(selected_reagents) if r]
                }
                st.session_state.jobs[job_index]['tray_configuration'] = tray_config
                st.success("Tray configuration saved successfully!")

        with col2:
            if job['tray_configuration']:
                st.subheader("Current Configuration")
                fig = go.Figure()
                for i, loc in enumerate(job['tray_configuration']['tray_locations']):
                    row = i // 4
                    col = i % 4
                    color = get_reagent_color(loc['reagent_code'])
                    fig.add_trace(go.Scatter(
                        x=[col, col+1, col+1, col, col],
                        y=[row, row, row+1, row+1, row],
                        fill="toself",
                        fillcolor=color,
                        line=dict(color="black", width=1),
                        mode="lines",
                        name=f"LOC-{i+1}",
                        text=f"LOC-{i+1}<br>{loc['reagent_code']}",
                        hoverinfo="text"
                    ))
                fig.update_layout(
                    title="Tray Configuration",
                    showlegend=False,
                    height=400,
                    width=400,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig)

def inventory_management():
    st.header("Inventory Management")

    col1, col2 = st.columns(2)

    with col1:
        with st.form("new_inventory"):
            reagent = st.text_input("Reagent")
            batch_number = st.text_input("Batch Number")
            quantity = st.number_input("Quantity", min_value=0)
            if st.form_submit_button("Add Inventory"):
                new_item = {
                    "id": generate_id(),
                    "reagent": reagent,
                    "batch_number": batch_number,
                    "quantity": quantity
                }
                st.session_state.inventory.append(new_item)
                st.success("Inventory item added successfully!")

    with col2:
        if st.session_state.inventory:
            df = pd.DataFrame(st.session_state.inventory)
            st.dataframe(df)
        else:
            st.info("No inventory items yet.")

def production_and_qc():
    st.header("Production and QC")
    
    job_id = st.selectbox("Select Job", options=[job['id'] for job in st.session_state.jobs if job['status'] == 'Open' and job['tray_configuration']])
    
    if job_id:
        job_index = next(i for i, job in enumerate(st.session_state.jobs) if job['id'] == job_id)
        job = st.session_state.jobs[job_index]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Production Steps")
            steps = ["Pour reagents into tray", "Seal tray chambers", "Apply tray label", "Package tray in box"]
            completed_steps = []
            for step in steps:
                if st.checkbox(step):
                    completed_steps.append(step)
            
            st.subheader("QC Checklist")
            qc_items = ["Verify reagent volumes", "Check tray seal integrity", "Confirm label accuracy", "Inspect packaging"]
            completed_qc = []
            for item in qc_items:
                if st.checkbox(item):
                    completed_qc.append(item)
            
            if st.button("Complete Production & QC"):
                production_record = {
                    "completed_steps": completed_steps,
                    "completed_qc": completed_qc,
                    "date": datetime.now().isoformat()
                }
                st.session_state.jobs[job_index]['production_record'] = production_record
                st.success("Production and QC record saved!")

        with col2:
            if job['production_record']:
                st.subheader("Production Record")
                st.write(f"Date: {job['production_record']['date']}")
                st.write("Completed Steps:")
                for step in job['production_record']['completed_steps']:
                    st.write(f"- {step}")
                st.write("Completed QC:")
                for item in job['production_record']['completed_qc']:
                    st.write(f"- {item}")

def shipping_and_logging():
    st.header("Shipping and Logging")
    
    job_id = st.selectbox("Select Job", options=[job['id'] for job in st.session_state.jobs if job['status'] == 'Open' and job['production_record']])
    
    if job_id:
        job_index = next(i for i, job in enumerate(st.session_state.jobs) if job['id'] == job_id)
        job = st.session_state.jobs[job_index]
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("shipment_form"):
                tracking_number = st.text_input("Tracking Number")
                shipping_date = st.date_input("Shipping Date")
                if st.form_submit_button("Log Shipment"):
                    shipment_info = {
                        "tracking_number": tracking_number,
                        "shipping_date": shipping_date.isoformat()
                    }
                    st.session_state.jobs[job_index]['shipment_info'] = shipment_info
                    st.success("Shipment logged successfully!")

        with col2:
            if job['shipment_info']:
                st.subheader("Shipment Information")
                st.write(f"Tracking Number: {job['shipment_info']['tracking_number']}")
                st.write(f"Shipping Date: {job['shipment_info']['shipping_date']}")

        if job['shipment_info']:
            if st.button("Close Job"):
                st.session_state.jobs[job_index]['status'] = 'Closed'
                st.success("Job closed successfully!")

def equipment_integration():
    st.header("Equipment Integration")

    for equipment in st.session_state.equipment:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader(equipment['name'])
        with col2:
            st.write(f"Status: {equipment['status']}")
            st.write(f"Last Reading: {equipment['last_reading']}")
        with col3:
            if st.button(f"Calibrate {equipment['name']}"):
                st.success(f"{equipment['name']} calibrated successfully!")

    st.subheader("Barcode Scanner")
    barcode = st.text_input("Scan Barcode")
    if st.button("Process Barcode"):
        st.success(f"Barcode {barcode} processed successfully!")

def analytics():
    st.header("Analytics")

    # Job Trends
    job_trends = pd.DataFrame(st.session_state.jobs)
    if not job_trends.empty:
        job_trends['date'] = pd.to_datetime(job_trends['date'])
        job_trends = job_trends.groupby('date').size().reset_index(name='count')
        fig = px.line(job_trends, x='date', y='count', title='Job Trends')
        st.plotly_chart(fig)

    # Job Status Distribution
    if st.session_state.jobs:
        status_counts = pd.DataFrame(st.session_state.jobs)['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.pie(status_counts, values='Count', names='Status', title='Job Status Distribution')
        st.plotly_chart(fig)

    # Experiment Popularity
    if st.session_state.jobs:
        experiment_counts = pd.DataFrame([
            job['tray_configuration']['tray_locations'] 
            for job in st.session_state.jobs 
            if job['tray_configuration'] and isinstance(job['tray_configuration'], dict)
        ]).explode().value_counts().reset_index()
        experiment_counts.columns = ['Experiment', 'Count']
        fig = px.pie(experiment_counts, values='Count', names='Experiment', title='Experiment Popularity')
        st.plotly_chart(fig)

    # Inventory Levels
    if st.session_state.inventory:
        inventory_df = pd.DataFrame(st.session_state.inventory)
        fig = px.bar(inventory_df, x='reagent', y='quantity', title='Inventory Levels')
        st.plotly_chart(fig)

    # Production Efficiency
    if st.session_state.jobs:
        production_times = [
            (datetime.fromisoformat(job['production_record']['date']) - datetime.fromisoformat(job['date'])).days
            for job in st.session_state.jobs
            if job['production_record'] and isinstance(job['production_record'], dict) and 'date' in job['production_record']
        ]
        if production_times:
            avg_production_time = sum(production_times) / len(production_times)
            st.metric("Average Production Time", f"{avg_production_time:.2f} days")

            fig = px.histogram(production_times, title="Production Time Distribution")
            fig.update_layout(xaxis_title="Days", yaxis_title="Frequency")
            st.plotly_chart(fig)

    # Customer Analysis
    if st.session_state.jobs:
        customer_jobs = pd.DataFrame(st.session_state.jobs).groupby('customer').size().reset_index(name='job_count')
        customer_jobs = customer_jobs.sort_values('job_count', ascending=False)
        fig = px.bar(customer_jobs, x='customer', y='job_count', title='Jobs per Customer')
        st.plotly_chart(fig)

    # Equipment Uptime
    equipment_status = pd.DataFrame(st.session_state.equipment)
    online_equipment = equipment_status[equipment_status['status'] == 'Online'].shape[0]
    total_equipment = equipment_status.shape[0]
    uptime_percentage = (online_equipment / total_equipment) * 100
    st.metric("Equipment Uptime", f"{uptime_percentage:.2f}%")

    # Reagent Usage
    if st.session_state.jobs:
        reagent_usage = pd.DataFrame([
            loc['reagent_code']
            for job in st.session_state.jobs
            if job['tray_configuration'] and isinstance(job['tray_configuration'], dict) and 'tray_locations' in job['tray_configuration']
            for loc in job['tray_configuration']['tray_locations']
            if isinstance(loc, dict) and 'reagent_code' in loc
        ]).value_counts().reset_index()
        reagent_usage.columns = ['Reagent', 'Usage Count']
        fig = px.bar(reagent_usage, x='Reagent', y='Usage Count', title='Reagent Usage Frequency')
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import uuid

# Import the ReagentOptimizer
from reagent_optimizer import ReagentOptimizer

# Set page config
st.set_page_config(page_title="Reagent Tray LIMS", page_icon="🧪", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stExpander {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stDataFrame {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'jobs' not in st.session_state:
    st.session_state.jobs = []

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

# Job Management
def job_management():
    st.header("Job Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("new_job"):
            customer = st.text_input("Customer Name")
            analyst = st.text_input("Analyst Name")
            date = st.date_input("Request Date")
            if st.form_submit_button("Create New Job"):
                new_job = {
                    "id": generate_id(),
                    "customer": customer,
                    "analyst": analyst,
                    "date": date.strftime("%Y-%m-%d"),
                    "status": "Open",
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

# Tray Configuration
def tray_configuration():
    st.header("Tray Configuration")
    
    job_id = st.selectbox("Select Job", options=[job['id'] for job in st.session_state.jobs if job['status'] == 'Open'])
    
    if job_id:
        optimizer = ReagentOptimizer()
        
        col1, col2 = st.columns(2)
        
        with col1:
            available_experiments = optimizer.get_available_experiments()
            selected_experiments = st.multiselect(
                "Select Experiments",
                options=[exp['id'] for exp in available_experiments],
                format_func=lambda x: next(exp['name'] for exp in available_experiments if exp['id'] == x)
            )
            
            if st.button("Optimize Configuration"):
                if not selected_experiments:
                    st.warning("Please select at least one experiment.")
                else:
                    try:
                        config = optimizer.optimize_tray_configuration(selected_experiments)
                        job_index = next(i for i, job in enumerate(st.session_state.jobs) if job['id'] == job_id)
                        st.session_state.jobs[job_index]['tray_configuration'] = config
                        st.success("Tray configuration optimized and saved successfully!")
                    except ValueError as e:
                        st.error(str(e))
        
        with col2:
            job = next(job for job in st.session_state.jobs if job['id'] == job_id)
            if job['tray_configuration']:
                config = job['tray_configuration']
                
                # Visualize tray configuration
                fig = go.Figure()
                for i, loc in enumerate(config['tray_locations']):
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

                fig.update_layout(
                    title="Optimized Tray Configuration",
                    showlegend=False,
                    height=400,
                    width=400,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig)

                st.subheader("Results Summary")
                tray_life = min(result["total_tests"] for result in config["results"].values())
                st.metric("Tray Life (Tests)", tray_life)

                for exp_num, result in config["results"].items():
                    with st.expander(f"{result['name']} (#{exp_num}) - {result['total_tests']} total tests"):
                        for i, set_info in enumerate(result["sets"]):
                            st.markdown(f"**{'Primary' if i == 0 else 'Additional'} Set {i+1}:**")
                            set_df = pd.DataFrame([
                                {
                                    "Reagent": placement["reagent_code"],
                                    "Location": f"LOC-{placement['location'] + 1}",
                                    "Tests Possible": placement["tests"]
                                }
                                for placement in set_info["placements"]
                            ])
                            st.dataframe(set_df)
                            st.markdown(f"**Tests from this set:** {set_info['tests_per_set']}")
                            st.markdown("---")

# Production and QC
def production_and_qc():
    st.header("Production and QC")
    
    job_id = st.selectbox("Select Job", options=[job['id'] for job in st.session_state.jobs if job['status'] == 'Open' and job['tray_configuration']])
    
    if job_id:
        job_index = next(i for i, job in enumerate(st.session_state.jobs) if job['id'] == job_id)
        job = st.session_state.jobs[job_index]
        
        col1, col2 = st.columns(2)
        
        with col1:
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
                production_record = {
                    "completed_steps": completed_steps,
                    "completed_qc": completed_qc,
                    "date": datetime.now().strftime("%Y-%m-%d")
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

# Shipping and Logging
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
                        "shipping_date": shipping_date.strftime("%Y-%m-%d")
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

# Job Search and Reporting
def job_search_and_reporting():
    st.header("Job Search and Reporting")
    
    search_term = st.text_input("Search by Customer Name or Analyst")
    status_filter = st.multiselect("Filter by Status", options=['Open', 'Closed'])
    
    filtered_jobs = [job for job in st.session_state.jobs if 
                     (search_term.lower() in job['customer'].lower() or 
                      search_term.lower() in job['analyst'].lower()) and
                     (not status_filter or job['status'] in status_filter)]
    
    if filtered_jobs:
        df = pd.DataFrame(filtered_jobs)
        st.dataframe(df)
        
        if st.button("Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="job_report.csv",
                mime="text/csv"
            )
    else:
        st.info("No jobs found matching the search criteria.")

# Main app
def main():
    st.title("🧪 Reagent Tray LIMS")

    # Sidebar navigation
    page = st.sidebar.radio("Navigate", ["Job Management", "Tray Configuration", "Production & QC", "Shipping & Logging", "Job Search & Reporting"])

    if page == "Job Management":
        job_management()
    elif page == "Tray Configuration":
        tray_configuration()
    elif page == "Production & QC":
        production_and_qc()
    elif page == "Shipping & Logging":
        shipping_and_logging()
    elif page == "Job Search & Reporting":
        job_search_and_reporting()

if __name__ == "__main__":
    main()

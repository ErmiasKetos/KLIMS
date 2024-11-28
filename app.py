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
    .menu-item {
        display: inline-block;
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
    }
    .menu-item:hover {
        background-color: #45a049;
    }
    .dashboard-card {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

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

def send_email(recipient, subject, body):
    # Replace with your email configuration
    sender_email = "your_email@example.com"
    sender_password = "your_email_password"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

def send_slack_message(channel, message):
    # Replace with your Slack API token
    slack_token = "your_slack_api_token"
    client = slack.WebClient(token=slack_token)
    client.chat_postMessage(channel=channel, text=message)

def notify_job_status(job, status):
    email_subject = f"Job {job['id']} Status Update"
    email_body = f"Job {job['id']} for customer {job['customer']} is now {status}."
    send_email(job['email'], email_subject, email_body)

    slack_message = f"Job {job['id']} for customer {job['customer']} is now {status}."
    send_slack_message("#lab-notifications", slack_message)

# Dashboard
def dashboard():
    st.header("Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("Total Jobs")
        st.metric("Jobs", len(st.session_state.jobs))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("Open Jobs")
        open_jobs = len([job for job in st.session_state.jobs if job['status'] == 'Open'])
        st.metric("Open", open_jobs)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("Closed Jobs")
        closed_jobs = len([job for job in st.session_state.jobs if job['status'] == 'Closed'])
        st.metric("Closed", closed_jobs)
        st.markdown('</div>', unsafe_allow_html=True)

    # Job Status Chart
    status_counts = pd.DataFrame(st.session_state.jobs).groupby('status').size().reset_index(name='count')
    fig = px.pie(status_counts, values='count', names='status', title='Job Status Distribution')
    st.plotly_chart(fig)

    # Recent Jobs
    st.subheader("Recent Jobs")
    recent_jobs = sorted(st.session_state.jobs, key=lambda x: x['date'], reverse=True)[:5]
    if recent_jobs:
        df = pd.DataFrame(recent_jobs)
        st.dataframe(df)
    else:
        st.info("No recent jobs.")

# Job Management
def job_management():
    st.header("Job Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("new_job"):
            customer = st.text_input("Customer Name")
            analyst = st.text_input("Analyst Name")
            email = st.text_input("Email")
            date = st.date_input("Request Date")
            if st.form_submit_button("Create New Job"):
                new_job = {
                    "id": generate_id(),
                    "customer": customer,
                    "analyst": analyst,
                    "email": email,
                    "date": date.strftime("%Y-%m-%d"),
                    "status": "Open",
                    "tray_configuration": None,
                    "production_record": None,
                    "shipment_info": None
                }
                st.session_state.jobs.append(new_job)
                notify_job_status(new_job, "received")
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
                        notify_job_status(st.session_state.jobs[job_index], "in progress")
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
                notify_job_status(st.session_state.jobs[job_index], "production completed")
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
                    notify_job_status(st.session_state.jobs[job_index], "shipped")
                    st.success("Shipment logged successfully!")

        with col2:
            if job['shipment_info']:
                st.subheader("Shipment Information")
                st.write(f"Tracking Number: {job['shipment_info']['tracking_number']}")
                st.write(f"Shipping Date: {job['shipment_info']['shipping_date']}")

        if job['shipment_info']:
            if st.button("Close Job"):
                st.session_state.jobs[job_index]['status'] = 'Closed'
                notify_job_status(st.session_state.jobs[job_index], "closed")
                st.success("Job closed successfully!")

# Analytics
def analytics():
    st.header("Analytics")

    # Job Status Over Time
    jobs_df = pd.DataFrame(st.session_state.jobs)
    jobs_df['date'] = pd.to_datetime(jobs_df['date'])
    jobs_df = jobs_df.sort_values('date')

    status_counts = jobs_df.groupby(['date', 'status']).size().unstack(fill_value=0).cumsum()
    fig = px.area(status_counts, title="Job Status Over Time")
    st.plotly_chart(fig)

    # Average Job Duration
    closed_jobs = jobs_df[jobs_df['status'] == 'Closed']
    if not closed_jobs.empty:
        closed_jobs['duration'] = (pd.to_datetime(closed_jobs['shipment_info'].apply(lambda x: x['shipping_date'] if x else None)) - closed_jobs['date']).dt.days
        avg_duration = closed_jobs['duration'].mean()
        st.metric("Average Job Duration (days)", f"{avg_duration:.2f}")

    # Top Customers
    top_customers = jobs_df['customer'].value_counts().head(5)
    fig = px.bar(top_customers, title="Top 5 Customers")
    st.plotly_chart(fig)

    # Experiment Popularity
    experiment_counts = jobs_df['tray_configuration'].apply(lambda x: x['results'].keys() if x else []).explode().value_counts()
    fig = px.pie(experiment_counts, values=experiment_counts.values, names=experiment_counts.index, title="Experiment Popularity")
    st.plotly_chart(fig)

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
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="job_report.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No jobs found matching the search criteria.")

# Main app
def main():
    st.title("🧪 Reagent Tray LIMS")

    # Horizontal top menu
    menu_items = ["Dashboard", "Job Management", "Tray Configuration", "Production & QC", "Shipping & Logging", "Analytics", "Job Search & Reporting"]
    menu_html = "".join(f'<a class="menu-item" href="#{item.lower().replace(" ", "-")}">{item}</a>' for item in menu_items)
    st.markdown(f'<div style="text-align: center;">{menu_html}</div>', unsafe_allow_html=True)

    # Page navigation
    for item in menu_items:
        if st.button(item, key=f"menu_{item}"):
            st.session_state.page = item

    # Display the selected page
    if st.session_state.page == "Dashboard":
        dashboard()
    elif st.session_state.page == "Job Management":
        job_management()
    elif st.session_state.page == "Tray Configuration":
        tray_configuration()
    elif st.session_state.page == "Production & QC":
        production_and_qc()
    elif st.session_state.page == "Shipping & Logging":
        shipping_and_logging()
    elif st.session_state.page == "Analytics":
        analytics()
    elif st.session_state.page == "Job Search & Reporting":
        job_search_and_reporting()

if __name__ == "__main__":
    main()

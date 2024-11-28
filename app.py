import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from reagent_optimizer import ReagentOptimizer
import base64
from io import BytesIO
from PIL import Image
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Set page config
st.set_page_config(
    page_title="Reagent Tray LIMS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f0f8ff;
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
        padding-top: 2rem;
    }
    .css-1d391kg {
        padding-top: 3rem;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Set background image
# Uncomment the following line when you have a background.png file
# set_png_as_page_bg('background.png')

# Email integration
def send_email_notification(to_email, subject, body):
    from_email = "your-email@example.com"
    password = os.environ.get("EMAIL_PASSWORD")

    if not password:
        st.warning("Email integration not configured. Skipping notification.")
        return False

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# Main function
def main():
    st.title("🧪 Reagent Tray LIMS")

    # Horizontal menu using st.selectbox
    menu_options = ["Dashboard", "Requests", "Tray Configuration", "Inventory", "Production & QC", "Shipping & Logging", "Analytics"]
    selected = st.selectbox("Select a page", menu_options)

    if selected == "Dashboard":
        show_dashboard()
    elif selected == "Requests":
        show_requests()
    elif selected == "Tray Configuration":
        show_tray_configuration()
    elif selected == "Inventory":
        show_inventory()
    elif selected == "Production & QC":
        show_production_and_qc()
    elif selected == "Shipping & Logging":
        show_shipping_and_logging()
    elif selected == "Analytics":
        show_analytics()

def show_dashboard():
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Open Requests", value=15)
    with col2:
        st.metric(label="Trays in Production", value=8)
    with col3:
        st.metric(label="Shipped This Week", value=22, delta=5)

    # Sample data for charts
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    requests = pd.Series(range(1, 32), index=dates).cumsum() + pd.Series(np.random.randn(31) * 5, index=dates).cumsum()
    production = requests.shift(2).fillna(0)
    shipped = production.shift(3).fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=requests, mode='lines', name='Requests'))
    fig.add_trace(go.Scatter(x=dates, y=production, mode='lines', name='Production'))
    fig.add_trace(go.Scatter(x=dates, y=shipped, mode='lines', name='Shipped'))
    fig.update_layout(title='Monthly Overview', xaxis_title='Date', yaxis_title='Count')
    st.plotly_chart(fig, use_container_width=True)

def show_requests():
    st.header("Request Management")
    
    # Form for new requests
    with st.form("new_request"):
        col1, col2 = st.columns(2)
        with col1:
            customer = st.text_input("Customer Name")
        with col2:
            date = st.date_input("Request Date")
        submitted = st.form_submit_button("Add Request")
        if submitted:
            # Add request to database (placeholder)
            st.success(f"Request added for {customer} on {date}")
            send_email_notification("requester@example.com", "New Request Received", f"Your request for {date} has been received and is being processed.")

    # Display existing requests
    requests_data = [
        {"id": 1, "customer": "Lab A", "date": "2024-11-28", "status": "Open"},
        {"id": 2, "customer": "Lab B", "date": "2024-11-29", "status": "In Progress"},
        {"id": 3, "customer": "Lab C", "date": "2024-11-30", "status": "Closed"},
    ]
    df = pd.DataFrame(requests_data)
    st.dataframe(df)

def show_tray_configuration():
    st.header("Tray Configuration")
    
    optimizer = ReagentOptimizer()
    experiments = optimizer.get_available_experiments()

    selected_experiments = st.multiselect("Select experiments", options=[f"{exp['id']}: {exp['name']}" for exp in experiments])
    selected_ids = [int(exp.split(':')[0]) for exp in selected_experiments]

    if st.button("Optimize Configuration"):
        if not selected_ids:
            st.error("Please select at least one experiment")
        else:
            try:
                with st.spinner("Optimizing tray configuration..."):
                    config = optimizer.optimize_tray_configuration(selected_ids)
                st.session_state.config = config
                st.success("Configuration optimized successfully!")
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
        col1, col2, col3 = st.columns(3)
        with col1:
            reagent = st.text_input("Reagent")
        with col2:
            batch_number = st.text_input("Batch Number")
        with col3:
            quantity = st.number_input("Quantity", min_value=0)
        submitted = st.form_submit_button("Add Item")
        if submitted:
            # Add item to inventory (placeholder)
            st.success(f"Added {quantity} of {reagent} (Batch: {batch_number}) to inventory")

    # Display current inventory
    inventory_data = [
        {"id": 1, "reagent": "KR1E", "batch_number": "B001", "quantity": 1000},
        {"id": 2, "reagent": "KR1S", "batch_number": "B002", "quantity": 500},
        {"id": 3, "reagent": "KR2S", "batch_number": "B003", "quantity": 750},
    ]
    df = pd.DataFrame(inventory_data)
    st.dataframe(df)

    # Inventory level visualization
    fig = px.bar(df, x='reagent', y='quantity', title='Current Inventory Levels')
    st.plotly_chart(fig, use_container_width=True)

def show_production_and_qc():
    st.header("Production & QC")
    
    # Production steps
    st.subheader("Production Steps")
    steps = ["Pour reagents", "Seal tray", "Apply label", "Package"]
    for step in steps:
        st.checkbox(step)

    # QC checklist
    st.subheader("QC Checklist")
    qc_items = ["Volume check", "Seal integrity", "Label accuracy", "Packaging quality"]
    for item in qc_items:
        st.checkbox(item)

    if st.button("Complete Production & QC"):
        st.success("Production and QC completed successfully!")
        send_email_notification("requester@example.com", "Tray Production Complete", "Your requested tray has completed production and quality control checks.")

def show_shipping_and_logging():
    st.header("Shipping & Logging")
    
    # Form for logging new shipments
    with st.form("new_shipment"):
        col1, col2, col3 = st.columns(3)
        with col1:
            customer = st.text_input("Customer")
        with col2:
            tracking_number = st.text_input("Tracking Number")
        with col3:
            ship_date = st.date_input("Ship Date")
        submitted = st.form_submit_button("Log Shipment")
        if submitted:
            # Log shipment (placeholder)
            st.success(f"Shipment logged for {customer} with tracking number {tracking_number}")
            send_email_notification("requester@example.com", "Shipment Sent", f"Your order has been shipped with tracking number {tracking_number}")

    # Display shipment log
    shipments_data = [
        {"id": 1, "customer": "Lab A", "tracking_number": "1234567890", "ship_date": "2024-11-28"},
        {"id": 2, "customer": "Lab B", "tracking_number": "0987654321", "ship_date": "2024-11-29"},
    ]
    df = pd.DataFrame(shipments_data)
    st.dataframe(df)

def show_analytics():
    st.header("Analytics")

    # Sample data for analytics
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    data = pd.DataFrame({
        'date': dates,
        'requests': np.random.randint(1, 10, size=len(dates)),
        'production': np.random.randint(1, 8, size=len(dates)),
        'shipped': np.random.randint(1, 7, size=len(dates))
    })
    data['cumulative_requests'] = data['requests'].cumsum()
    data['cumulative_production'] = data['production'].cumsum()
    data['cumulative_shipped'] = data['shipped'].cumsum()

    # Yearly overview
    st.subheader("Yearly Overview")
    fig = px.line(data, x='date', y=['cumulative_requests', 'cumulative_production', 'cumulative_shipped'],
                  title='Cumulative Yearly Activity')
    st.plotly_chart(fig, use_container_width=True)

    # Monthly breakdown
    st.subheader("Monthly Breakdown")
    monthly_data = data.resample('M', on='date').sum()
    fig = px.bar(monthly_data, x=monthly_data.index, y=['requests', 'production', 'shipped'],
                 title='Monthly Activity Breakdown')
    st.plotly_chart(fig, use_container_width=True)

    # Top customers
    st.subheader("Top Customers")
    top_customers = pd.DataFrame({
        'customer': ['Lab A', 'Lab B', 'Lab C', 'Lab D', 'Lab E'],
        'orders': [120, 80, 60, 40, 30]
    })
    fig = px.pie(top_customers, values='orders', names='customer', title='Top Customers by Orders')
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()


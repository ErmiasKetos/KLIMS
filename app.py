import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reagent_optimizer import ReagentOptimizer
import sqlite3
from datetime import datetime
from io import BytesIO
import xlsxwriter

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
    .css-1d391kg {
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)
   

# Page config
st.set_page_config(page_title="KCF Trays LIMS", page_icon="🧪", layout="wide")

def search_and_reports():
   st.header("Search & Reports")
   
   search_type = st.radio("Search By", 
       ["Work Order", "Customer", "Date Range", "Status"],
       key="search_type_radio"
   )
   
   conn = create_connection()
   c = conn.cursor()
   
   if search_type == "Work Order":
       wo_id = st.text_input("Work Order ID", key="search_wo_id_input")
       if wo_id:
           results = search_by_wo(c, wo_id)
           display_search_results(results)
           
   elif search_type == "Customer":
       customer = st.text_input("Customer Name", key="search_customer_input")
       if customer:
           results = search_by_customer(c, customer)
           display_search_results(results)
           
   elif search_type == "Date Range":
       col1, col2 = st.columns(2)
       start_date = col1.date_input("Start Date", key="search_start_date")
       end_date = col2.date_input("End Date", key="search_end_date")
       if st.button("Search", key="date_search_button"):
           results = search_by_date(c, start_date, end_date)
           display_search_results(results)
   
   else:  # Status
       status = st.selectbox("Status", 
           ["Created", "Configured", "Production Complete", "Shipped", "All"],
           key="status_select"
       )
       if st.button("Search", key="status_search_button"):
           results = search_by_status(c, status)
           display_search_results(results)

   st.divider()


   # Report generation 
   st.subheader("Generate Reports")
   report_type = st.selectbox("Report Type",
       ["Work Order Summary", "Production Statistics", 
        "Shipping Log", "Inventory Status"],
       key="report_type_select"
   )

   if st.button("Generate Report", key="generate_report_button"):
       if report_type == "Work Order Summary":
           generate_wo_summary(c)
       elif report_type == "Production Statistics":
           generate_production_stats(c)  
       elif report_type == "Shipping Log":
           generate_shipping_log(c)
       else:
           generate_inventory_report(c)
           
   conn.close()

def create_connection():
    return sqlite3.connect('reagent_lims.db')

def setup_database():
    conn = create_connection()
    c = conn.cursor()
    
    # Create tables with updated schema
    c.execute('''CREATE TABLE IF NOT EXISTS work_orders
                 (id TEXT PRIMARY KEY,
                  customer TEXT,
                  requester TEXT,
                  date TEXT,
                  status TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS trays
                 (id INTEGER PRIMARY KEY,
                  wo_id TEXT,
                  customer TEXT,
                  requester TEXT,
                  date TEXT,
                  configuration TEXT,
                  FOREIGN KEY(wo_id) REFERENCES work_orders(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS production
                 (id INTEGER PRIMARY KEY,
                  tray_id INTEGER,
                  wo_id TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  status TEXT,
                  FOREIGN KEY(tray_id) REFERENCES trays(id),
                  FOREIGN KEY(wo_id) REFERENCES work_orders(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shipping
                 (id INTEGER PRIMARY KEY,
                  tray_id INTEGER,
                  wo_id TEXT,
                  customer TEXT,
                  requester TEXT,
                  tracking_number TEXT,
                  ship_date TEXT,
                  FOREIGN KEY(tray_id) REFERENCES trays(id),
                  FOREIGN KEY(wo_id) REFERENCES work_orders(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY,
                  wo_id TEXT,
                  reagent TEXT,
                  batch TEXT,
                  quantity INTEGER,
                  date TEXT,
                  status TEXT,
                  FOREIGN KEY(wo_id) REFERENCES work_orders(id))''')
    
    conn.commit()
    conn.close()

def generate_wo_number():
    conn = create_connection()
    c = conn.cursor()
    
    now = datetime.now()
    year = now.strftime('%y')
    month = now.strftime('%m')
    
    pattern = f'WO-{year}-{month}-%'
    c.execute("SELECT id FROM work_orders WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (pattern,))
    last_wo = c.fetchone()
    
    if last_wo:
        last_num = int(last_wo[0].split('-')[-1])
        new_num = str(last_num + 1).zfill(4)
    else:
        new_num = '0001'
    
    conn.close()
    return f"WO-{year}-{month}-{new_num}"

def get_next_step(wo_id):
    conn = create_connection()
    c = conn.cursor()
    
    c.execute("SELECT status FROM work_orders WHERE id=?", (wo_id,))
    status = c.fetchone()[0]
    
    if status == 'Open':
        c.execute("SELECT id FROM trays WHERE wo_id=?", (wo_id,))
        if not c.fetchone():
            conn.close()
            return "Configure Tray", 2
        
        c.execute("SELECT status FROM production WHERE wo_id=?", (wo_id,))
        prod_status = c.fetchone()
        if not prod_status or prod_status[0] != 'Complete':
            conn.close()
            return "Complete Production", 4
        
        c.execute("SELECT id FROM shipping WHERE wo_id=?", (wo_id,))
        if not c.fetchone():
            conn.close()
            return "Ship Tray", 5
    
    conn.close()
    return "Work Order Complete", None

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
    return 'lightgray'

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
            text=f"<b>LOC-{i+1}</b><br>{'<b>' + loc['reagent_code'] if loc else 'Empty</b>'}<br>Tests: {loc['tests_possible'] if loc else 'N/A'}<br>Exp: #{loc['experiment'] if loc else 'N/A'}",
            showarrow=False,
            font=dict(color="black", size=14),
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

def display_results(config, selected_experiments):
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Tray Configuration")
        fig = create_tray_visualization(config)
        st.plotly_chart(fig, use_container_width=true)

    with col2:
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
        st.dataframe(results_df, use_container_width=True)

    st.subheader("Detailed Results")
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
                st.dataframe(set_df, use_container_width=True)
                st.markdown(f"**Tests from this set:** {set_info['tests_per_set']}")
                st.markdown("---")

def manage_work_orders():
    st.header("Work Orders")
    
    # Initialize session state for work order management
    if 'wo_created' not in st.session_state:
        st.session_state.wo_created = False
    
    with st.form("new_work_order"):
        cols = st.columns([2, 2, 1])
        customer = cols[0].text_input("Customer Name", key="wo_customer")
        requester = cols[0].text_input("Job Requester", key="wo_requester")
        date = cols[1].date_input("Date", key="wo_date")
        
        submitted = cols[2].form_submit_button("Create Work Order")
        if submitted and customer and requester:
            wo_id = generate_wo_number()
            conn = create_connection()
            c = conn.cursor()
            
            try:
                c.execute("""INSERT INTO work_orders 
                            (id, customer, requester, date, status) 
                            VALUES (?, ?, ?, ?, ?)""",
                         (wo_id, customer, requester, date.strftime('%Y-%m-%d'), 'Open'))
                
                c.execute("""INSERT INTO inventory 
                            (wo_id, date, status) 
                            VALUES (?, ?, ?)""",
                         (wo_id, date.strftime('%Y-%m-%d'), 'Created'))
                conn.commit()
                
                st.session_state.current_wo = wo_id
                st.session_state.wo_created = True
                
                next_step, tab_index = get_next_step(wo_id)
                st.session_state.next_tab = tab_index
                st.success(f"Work Order {wo_id} created. Next step: {next_step}")
                
            except Exception as e:
                st.error(f"Error creating work order: {str(e)}")
            finally:
                conn.close()

    # Display work orders
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT 
            wo.id, 
            wo.customer, 
            wo.requester, 
            wo.date, 
            wo.status,
            COALESCE(t.id, 'Pending') as tray_id,
            COALESCE(p.status, 'Not Started') as production_status,
            COALESCE(s.tracking_number, 'Not Shipped') as shipping_status
        FROM work_orders wo
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        ORDER BY wo.date DESC
    """)
    
    results = c.fetchall()
    conn.close()
    
    if results:
        df = pd.DataFrame(results, 
                         columns=['WO ID', 'Customer', 'Requester', 'Date', 'Status', 
                                 'Tray ID', 'Production', 'Shipping'])
        st.dataframe(df, use_container_width=True)
        
        # Add work order selection for configuration
        if st.button("Configure Selected Work Order"):
            selected_wo = st.session_state.get('selected_wo')
            if selected_wo:
                st.session_state.current_wo = selected_wo
                st.session_state.current_tab = 2  # Switch to Tray Configuration tab
def configure_tray():
    st.header("Tray Configuration")
    
    # Initialize session states
    if 'tray_state' not in st.session_state:
        st.session_state.tray_state = {
            'config': None,
            'selected_experiments': [],
            'experiment_selection_initialized': False
        }

    # Show current work order info
    if 'current_wo' in st.session_state:
        conn = create_connection()
        c = conn.cursor()
        c.execute("""SELECT id, customer, requester 
                     FROM work_orders WHERE id=?""", 
                 (st.session_state.current_wo,))
        wo = c.fetchone()
        conn.close()

        if wo:
            st.info(f"Configuring Work Order: {wo[0]} - {wo[1]} ({wo[2]})")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                optimizer = ReagentOptimizer()
                experiments = optimizer.get_available_experiments()
                
                st.subheader("Select Experiments")
                for exp in experiments:
                    key = f"exp_{wo[0]}_{exp['id']}"
                    if st.checkbox(f"{exp['id']}: {exp['name']}", 
                                 key=key,
                                 value=exp['id'] in st.session_state.tray_state['selected_experiments']):
                        if exp['id'] not in st.session_state.tray_state['selected_experiments']:
                            st.session_state.tray_state['selected_experiments'].append(exp['id'])
                    else:
                        if exp['id'] in st.session_state.tray_state['selected_experiments']:
                            st.session_state.tray_state['selected_experiments'].remove(exp['id'])

                if st.button("Optimize Configuration"):
                    if st.session_state.tray_state['selected_experiments']:
                        try:
                            with st.spinner("Optimizing configuration..."):
                                config = optimizer.optimize_tray_configuration(
                                    st.session_state.tray_state['selected_experiments']
                                )
                            st.session_state.tray_state['config'] = config
                            
                            # Save to database
                            save_configuration(wo[0], wo[1], wo[2], config)
                            
                            next_step, tab = get_next_step(wo[0])
                            st.success(f"Configuration saved. Next step: {next_step}")
                            st.session_state.current_tab = tab
                            
                        except Exception as e:
                            st.error(f"Configuration error: {str(e)}")
                    else:
                        st.warning("Please select at least one experiment")

            with col2:
                if st.session_state.tray_state['config']:
                    display_results(
                        st.session_state.tray_state['config'],
                        st.session_state.tray_state['selected_experiments']
                    )

def save_configuration(wo_id, customer, requester, config):
    conn = create_connection()
    c = conn.cursor()
    
    try:
        c.execute("""INSERT INTO trays 
                     (wo_id, customer, requester, date, configuration)
                     VALUES (?, ?, ?, ?, ?)""",
                 (wo_id, customer, requester, 
                  datetime.now().strftime('%Y-%m-%d'), 
                  str(config)))
        
        c.execute("""UPDATE inventory 
                     SET status = 'Configured'
                     WHERE wo_id = ?""", (wo_id,))
        conn.commit()
        
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        raise e
    finally:
        conn.close()

def manage_production():
    st.header("Production")
    
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.id, wo.id, wo.customer, wo.requester, t.date 
        FROM trays t
        JOIN work_orders wo ON t.wo_id = wo.id
        LEFT JOIN production p ON t.id = p.tray_id
        WHERE p.id IS NULL
    """)
    pending_trays = c.fetchall()
    conn.close()

    if not pending_trays:
        st.info("No trays pending production")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        tray = st.selectbox("Select Tray for Production",
                           pending_trays,
                           format_func=lambda x: f"{x[1]} - {x[2]} ({x[3]})")

        if tray:
            steps = {"Reagent Loading": ["Volume Check", "Placement Verification"],
                    "Sealing": ["Seal Integrity", "Temperature Check"],
                    "Labeling": ["Label Accuracy", "Barcode Verification"],
                    "QC": ["Visual Inspection", "Documentation"]}

            completed = {}
            for step, checks in steps.items():
                with st.expander(step):
                    completed[step] = all(
                        st.checkbox(check, key=f"{tray[0]}_{check}")
                        for check in checks
                    )

            if st.button("Complete Production") and all(completed.values()):
                complete_production(tray)
                st.success("Production completed")
                st.rerun()
def manage_inventory():
    st.header("Inventory Management")
    
    conn = create_connection()
    c = conn.cursor()
    
    # Work order status tracking
    st.subheader("Work Order Status")
    c.execute("""
        SELECT 
            i.wo_id,
            wo.customer,
            wo.requester,
            i.date,
            i.status,
            COALESCE(t.id, 'Pending') as tray_id,
            COALESCE(p.status, 'Not Started') as production_status,
            COALESCE(s.tracking_number, 'Not Shipped') as shipping_status
        FROM inventory i
        JOIN work_orders wo ON i.wo_id = wo.id
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        ORDER BY i.date DESC
    """)
    
    results = c.fetchall()
    if results:
        df = pd.DataFrame(results, columns=[
            'Work Order', 'Customer', 'Requester', 'Date', 
            'Status', 'Tray ID', 'Production', 'Shipping'
        ])
        st.dataframe(df, use_container_width=True)

        # Tray reagent usage for selected work order
        if 'current_wo' in st.session_state and 'config' in st.session_state.tray_state:
            st.subheader("Reagent Usage")
            config = st.session_state.tray_state['config']
            if config:
                reagents_df = pd.DataFrame([
                    {
                        'Work Order': st.session_state.current_wo,
                        'Reagent': loc['reagent_code'],
                        'Location': f"LOC-{idx + 1}",
                        'Tests': loc['tests_possible']
                    }
                    for idx, loc in enumerate(config['tray_locations'])
                    if loc
                ])
                st.dataframe(reagents_df, use_container_width=True)
    
    conn.close()

def manage_shipping():
    st.header("Shipping")
    
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.id, wo.id, wo.customer, wo.requester
        FROM trays t
        JOIN work_orders wo ON t.wo_id = wo.id
        JOIN production p ON t.id = p.tray_id
        LEFT JOIN shipping s ON t.id = s.tray_id
        WHERE p.status = 'Complete' AND s.id IS NULL
    """)
    ready_trays = c.fetchall()
    conn.close()

    if not ready_trays:
        st.info("No trays ready for shipping")
        return

    with st.form("shipping_form"):
        tray = st.selectbox("Select Tray",
                           ready_trays,
                           format_func=lambda x: f"{x[1]} - {x[2]} ({x[3]})")
        cols = st.columns(2)
        tracking = cols[0].text_input("Tracking Number")
        ship_date = cols[1].date_input("Ship Date")

        if st.form_submit_button("Process Shipment") and tracking:
            process_shipment(tray, tracking, ship_date)
            st.success("Shipment processed")
            st.rerun()

def complete_production(tray):
    conn = create_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("""
        INSERT INTO production (tray_id, wo_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (tray[0], tray[1], now, now, 'Complete'))
    
    c.execute("UPDATE inventory SET status = 'Production Complete' WHERE wo_id = ?", 
             (tray[1],))
    conn.commit()
    conn.close()

def process_shipment(tray, tracking, ship_date):
    conn = create_connection()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO shipping (tray_id, wo_id, customer, requester, tracking_number, ship_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tray[0], tray[1], tray[2], tray[3], tracking, ship_date.strftime('%Y-%m-%d')))
    
    c.execute("UPDATE work_orders SET status = 'Complete' WHERE id = ?", (tray[1],))
    c.execute("UPDATE inventory SET status = 'Shipped' WHERE wo_id = ?", (tray[1],))
    
    conn.commit()
    conn.close()

def show_dashboard():
    st.header("Dashboard")
    
    conn = create_connection()
    c = conn.cursor()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    today = datetime.now().strftime('%Y-%m-%d')
    
    metrics = {
        "Open Work Orders": "SELECT COUNT(*) FROM work_orders WHERE status='Open'",
        "Today's Trays": "SELECT COUNT(*) FROM trays WHERE date=?",
        "Production Complete": "SELECT COUNT(*) FROM production WHERE end_date=?",
        "Shipped Today": "SELECT COUNT(*) FROM shipping WHERE ship_date=?"
    }
    
    for col, (label, query) in zip([col1, col2, col3, col4], metrics.items()):
        c.execute(query, (today,) if '?' in query else ())
        col.metric(label, c.fetchone()[0])

    # Activity charts
    display_activity_charts(c)
    display_recent_activity(c)
    conn.close()

def display_activity_charts(c):
    st.subheader("30-Day Activity")
    
    queries = {
        'Work Orders': "SELECT date, COUNT(*) FROM work_orders WHERE date >= date('now', '-30 days') GROUP BY date",
        'Production': "SELECT end_date, COUNT(*) FROM production WHERE end_date >= date('now', '-30 days') GROUP BY end_date"
    }
    
    fig = go.Figure()
    for name, query in queries.items():
        c.execute(query)
        data = pd.DataFrame(c.fetchall(), columns=['date', 'count'])
        fig.add_trace(go.Scatter(x=data['date'], y=data['count'], 
                               name=name, mode='lines+markers'))
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def display_recent_activity(c):
    st.subheader("Recent Activity")
    
    c.execute("""
        SELECT 
            wo.id,
            wo.customer,
            wo.requester,
            CASE 
                WHEN s.ship_date IS NOT NULL THEN 'Shipped'
                WHEN p.end_date IS NOT NULL THEN 'Production Complete'
                WHEN t.date IS NOT NULL THEN 'Configured'
                ELSE 'Created'
            END as status,
            COALESCE(s.ship_date, p.end_date, t.date, wo.date) as date
        FROM work_orders wo
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        ORDER BY date DESC LIMIT 10
    """)
    
    df = pd.DataFrame(c.fetchall(), 
                     columns=['Work Order', 'Customer', 'Requester', 'Status', 'Date'])
    st.dataframe(df, use_container_width=True)

def main():
    st.title("🧪 Reagent LIMS")
    
    # Apply custom CSS
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] { gap: 2px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #F0F2F6;
            border-radius: 4px;
            padding: 10px;
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
        .stDataFrame, .stPlotlyChart {
            background-color: white;
            padding: 1rem;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Handle tab navigation
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 0
    
    tabs = st.tabs([
        "Dashboard", "Work Orders", "Tray Configuration",
        "Inventory", "Production", "Shipping", "Search & Reports"
    ])
    
    tab_functions = [
        show_dashboard, manage_work_orders, configure_tray,
        manage_inventory, manage_production, manage_shipping,
        search_and_reports
    ]
    
    for i, tab_function in enumerate(tab_functions):
        with tabs[i]:
            tab_function()

if __name__ == "__main__":
    setup_database()
    main()

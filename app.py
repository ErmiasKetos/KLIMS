import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reagent_optimizer import ReagentOptimizer
import sqlite3
from datetime import datetime
from io import BytesIO
import xlsxwriter



def search_and_reports():
    st.header("Search & Reports")
    
    search_type = st.radio("Search By", 
                          ["Work Order", "Customer", "Date Range", "Status"],
                          key="search_type_radio")
    
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
                            ["Created", "Configured", "Production Complete", 
                             "Shipped", "All"],
                            key="status_select")
        if st.button("Search", key="status_search_button"):
            results = search_by_status(c, status)
            display_search_results(results)
    
    st.divider()
    
    # Report generation
    st.subheader("Generate Reports")
    report_type = st.selectbox("Report Type",
                              ["Work Order Summary",
                               "Production Statistics",
                               "Shipping Log",
                               "Inventory Status"],
                              key="report_type_select")
    
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

def search_by_wo(c, wo_id):
    c.execute("""
        SELECT 
            wo.id,
            wo.customer,
            wo.requester,
            wo.date as created_date,
            COALESCE(t.date, 'Pending') as config_date,
            COALESCE(p.end_date, 'Pending') as prod_date,
            COALESCE(s.ship_date, 'Pending') as ship_date,
            COALESCE(s.tracking_number, 'Not Shipped') as tracking,
            i.status as current_status
        FROM work_orders wo
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        LEFT JOIN inventory i ON wo.id = i.wo_id
        WHERE wo.id LIKE ?
    """, (f"%{wo_id}%",))
    return c.fetchall()

def search_by_customer(c, customer):
    c.execute("""
        SELECT 
            wo.id,
            wo.customer,
            wo.requester,
            wo.date as created_date,
            COALESCE(t.date, 'Pending') as config_date,
            COALESCE(p.end_date, 'Pending') as prod_date,
            COALESCE(s.ship_date, 'Pending') as ship_date,
            COALESCE(s.tracking_number, 'Not Shipped') as tracking,
            i.status as current_status
        FROM work_orders wo
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        LEFT JOIN inventory i ON wo.id = i.wo_id
        WHERE wo.customer LIKE ?
    """, (f"%{customer}%",))
    return c.fetchall()

def search_by_date(c, start_date, end_date):
    c.execute("""
        SELECT 
            wo.id,
            wo.customer,
            wo.requester,
            wo.date as created_date,
            COALESCE(t.date, 'Pending') as config_date,
            COALESCE(p.end_date, 'Pending') as prod_date,
            COALESCE(s.ship_date, 'Pending') as ship_date,
            COALESCE(s.tracking_number, 'Not Shipped') as tracking,
            i.status as current_status
        FROM work_orders wo
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        LEFT JOIN inventory i ON wo.id = i.wo_id
        WHERE wo.date BETWEEN ? AND ?
    """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    return c.fetchall()

def search_by_status(c, status):
    if status == "All":
        c.execute("""
            SELECT 
                wo.id,
                wo.customer,
                wo.requester,
                wo.date as created_date,
                COALESCE(t.date, 'Pending') as config_date,
                COALESCE(p.end_date, 'Pending') as prod_date,
                COALESCE(s.ship_date, 'Pending') as ship_date,
                COALESCE(s.tracking_number, 'Not Shipped') as tracking,
                i.status as current_status
            FROM work_orders wo
            LEFT JOIN trays t ON wo.id = t.wo_id
            LEFT JOIN production p ON wo.id = p.wo_id
            LEFT JOIN shipping s ON wo.id = s.wo_id
            LEFT JOIN inventory i ON wo.id = i.wo_id
        """)
    else:
        c.execute("""
            SELECT 
                wo.id,
                wo.customer,
                wo.requester,
                wo.date as created_date,
                COALESCE(t.date, 'Pending') as config_date,
                COALESCE(p.end_date, 'Pending') as prod_date,
                COALESCE(s.ship_date, 'Pending') as ship_date,
                COALESCE(s.tracking_number, 'Not Shipped') as tracking,
                i.status as current_status
            FROM work_orders wo
            LEFT JOIN trays t ON wo.id = t.wo_id
            LEFT JOIN production p ON wo.id = p.wo_id
            LEFT JOIN shipping s ON wo.id = s.wo_id
            LEFT JOIN inventory i ON wo.id = i.wo_id
            WHERE i.status = ?
        """, (status,))
    return c.fetchall()

def display_search_results(results):
    if results:
        df = pd.DataFrame(results, columns=[
            'Work Order', 'Customer', 'Requester', 'Created', 
            'Configured', 'Production', 'Shipped', 'Tracking', 'Status'
        ])
        st.dataframe(df, use_container_width=True)
        
        if st.button("Export Results"):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "search_results.csv",
                "text/csv"
            )
    else:
        st.info("No results found")

def update_main():
    # Add Search & Reports tab
    tabs = st.tabs(["Dashboard", "Work Orders", "Tray Configuration",
                    "Inventory", "Production", "Shipping", "Search & Reports"])
    
    with tabs[0]: show_dashboard()
    with tabs[1]: manage_work_orders()
    with tabs[2]: configure_tray()
    with tabs[3]: manage_inventory()
    with tabs[4]: manage_production()
    with tabs[5]: manage_shipping()
    with tabs[6]: search_and_reports()

def generate_wo_summary(c):
    c.execute("""
        SELECT 
            wo.id,
            wo.customer,
            wo.requester,
            t.configuration,
            p.start_date,
            p.end_date,
            s.tracking_number,
            s.ship_date,
            i.status
        FROM work_orders wo
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        LEFT JOIN inventory i ON wo.id = i.wo_id
        ORDER BY wo.date DESC
    """)
    data = c.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=[
            'Work Order', 'Customer', 'Requester', 'Configuration',
            'Production Start', 'Production End', 'Tracking', 
            'Ship Date', 'Status'
        ])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df)
        with col2:
            st.metric("Total Work Orders", len(df))
            st.metric("Completed Orders", 
                     len(df[df['Status'] == 'Shipped']))
            
        export_to_excel(df, "wo_summary.xlsx")

def generate_production_stats(c):
    c.execute("""
        SELECT 
            p.wo_id,
            wo.customer,
            wo.requester,
            t.configuration,
            p.start_date,
            p.end_date,
            JULIANDAY(p.end_date) - JULIANDAY(p.start_date) as duration
        FROM production p
        JOIN work_orders wo ON p.wo_id = wo.id
        JOIN trays t ON p.tray_id = t.id
        WHERE p.status = 'Complete'
    """)
    data = c.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=[
            'Work Order', 'Customer', 'Requester', 'Configuration',
            'Start Date', 'End Date', 'Duration (days)'
        ])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df)
        with col2:
            st.metric("Avg Production Time", 
                     f"{df['Duration (days)'].mean():.1f} days")
            
        # Production timeline visualization
        fig = go.Figure()
        for _, row in df.iterrows():
            fig.add_trace(go.Bar(
                name=row['Work Order'],
                x=[row['Start Date']],
                y=[row['Duration (days)']],
                text=f"{row['Customer']}<br>{row['Duration (days)']:.1f} days",
                hoverinfo="text"
            ))
        
        fig.update_layout(
            title="Production Timeline",
            xaxis_title="Start Date",
            yaxis_title="Duration (days)",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        export_to_excel(df, "production_stats.xlsx")

def generate_shipping_log(c):
    c.execute("""
        SELECT 
            s.wo_id,
            wo.customer,
            wo.requester,
            s.tracking_number,
            s.ship_date,
            t.configuration,
            p.start_date as prod_start,
            p.end_date as prod_end
        FROM shipping s
        JOIN work_orders wo ON s.wo_id = wo.id
        JOIN trays t ON s.tray_id = t.id
        JOIN production p ON s.tray_id = p.tray_id
        ORDER BY s.ship_date DESC
    """)
    data = c.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=[
            'Work Order', 'Customer', 'Requester', 'Tracking',
            'Ship Date', 'Configuration', 'Production Start', 
            'Production End'
        ])
        
        st.dataframe(df)
        
        # Shipping metrics
        metrics_df = df.copy()
        metrics_df['Month'] = pd.to_datetime(df['Ship Date']).dt.to_period('M')
        monthly_stats = metrics_df.groupby('Month').size()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_stats.index.astype(str),
            y=monthly_stats.values,
            text=monthly_stats.values,
            textposition='auto',
        ))
        fig.update_layout(
            title="Monthly Shipments",
            xaxis_title="Month",
            yaxis_title="Number of Shipments"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        export_to_excel(df, "shipping_log.xlsx")

def generate_inventory_report(c):
    c.execute("""
        SELECT 
            i.wo_id,
            wo.customer,
            wo.requester,
            i.status,
            t.configuration,
            p.end_date as prod_date,
            s.ship_date
        FROM inventory i
        JOIN work_orders wo ON i.wo_id = wo.id
        LEFT JOIN trays t ON wo.id = t.wo_id
        LEFT JOIN production p ON wo.id = p.wo_id
        LEFT JOIN shipping s ON wo.id = s.wo_id
        ORDER BY i.date DESC
    """)
    data = c.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=[
            'Work Order', 'Customer', 'Requester', 'Status',
            'Configuration', 'Production Date', 'Ship Date'
        ])
        
        status_counts = df['Status'].value_counts()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df)
        with col2:
            for status, count in status_counts.items():
                st.metric(status, count)
        
        # Status distribution pie chart
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=.3
        )])
        fig.update_layout(title="Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        export_to_excel(df, "inventory_report.xlsx")

def export_to_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    excel_data = output.getvalue()
    st.download_button(
        label="Download Excel Report",
        data=excel_data,
        file_name=filename,
        mime="application/vnd.ms-excel"
    )

# Update imports at the top of the main file
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reagent_optimizer import ReagentOptimizer
import sqlite3
from datetime import datetime
from io import BytesIO
import xlsxwriter

# Page config
st.set_page_config(page_title="Reagent LIMS", page_icon="🧪", layout="wide")

# Database setup
def create_connection():
    conn = sqlite3.connect('reagent_lims.db')
    return conn


def setup_database():
    conn = create_connection()
    c = conn.cursor()
    
    # Drop existing tables if you need to rebuild
    c.execute("DROP TABLE IF EXISTS shipping")
    c.execute("DROP TABLE IF EXISTS production")
    c.execute("DROP TABLE IF EXISTS trays")
    c.execute("DROP TABLE IF EXISTS inventory")
    c.execute("DROP TABLE IF EXISTS work_orders")
    
    # Create tables with updated schema
    c.execute('''CREATE TABLE work_orders
                 (id TEXT PRIMARY KEY,
                  customer TEXT,
                  requester TEXT,
                  date TEXT,
                  status TEXT)''')
    
    conn = create_connection()
    c = conn.cursor()
    
    # Work Orders table with updated schema
    c.execute('''CREATE TABLE IF NOT EXISTS work_orders
                 (id TEXT PRIMARY KEY,
                  customer TEXT,
                  requester TEXT,
                  date TEXT,
                  status TEXT)''')
    
    # Trays table with expanded tracking
    c.execute('''CREATE TABLE IF NOT EXISTS trays
                 (id INTEGER PRIMARY KEY,
                  wo_id TEXT,
                  customer TEXT,
                  requester TEXT,
                  date TEXT,
                  configuration TEXT,
                  FOREIGN KEY(wo_id) REFERENCES work_orders(id))''')
    
    # Production tracking
    c.execute('''CREATE TABLE IF NOT EXISTS production
                 (id INTEGER PRIMARY KEY,
                  tray_id INTEGER,
                  wo_id TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  status TEXT,
                  FOREIGN KEY(tray_id) REFERENCES trays(id),
                  FOREIGN KEY(wo_id) REFERENCES work_orders(id))''')
    
    # Shipping with expanded tracking
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
    
    # Inventory with traceability
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
    
    # Get current date components
    now = datetime.now()
    year = now.strftime('%y')
    month = now.strftime('%m')
    
    # Find last WO number for current month
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
    
    # Check work order status
    c.execute("SELECT status FROM work_orders WHERE id=?", (wo_id,))
    status = c.fetchone()[0]
    
    if status == 'Open':
        # Check if tray configuration exists
        c.execute("SELECT id FROM trays WHERE wo_id=?", (wo_id,))
        if not c.fetchone():
            conn.close()
            return "Configure Tray", "tabs-2"
            
        # Check if production is complete
        c.execute("SELECT status FROM production WHERE wo_id=?", (wo_id,))
        prod_status = c.fetchone()
        if not prod_status or prod_status[0] != 'Complete':
            conn.close()
            return "Complete Production", "tabs-4"
            
        # Check if shipped
        c.execute("SELECT id FROM shipping WHERE wo_id=?", (wo_id,))
        if not c.fetchone():
            conn.close()
            return "Ship Tray", "tabs-5"
    
    conn.close()
    return "Work Order Complete", None

# Initialize database on startup
setup_database()

def manage_work_orders():
   st.header("Work Orders")
   
   with st.form("new_work_order"):
       cols = st.columns([2, 2, 1])
       customer = cols[0].text_input("Customer Name")
       requester = cols[0].text_input("Job Requester")
       date = cols[1].date_input("Date")
       
       submitted = cols[2].form_submit_button("Create Work Order")
       if submitted and customer and requester:
           wo_id = generate_wo_number()
           conn = create_connection()
           c = conn.cursor()
           
           c.execute("""INSERT INTO work_orders 
                       (id, customer, requester, date, status) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (wo_id, customer, requester, date.strftime('%Y-%m-%d'), 'Open'))
           conn.commit()
           
           # Initialize configuration state
           st.session_state.pending_configuration = True
           st.session_state.current_wo = wo_id
           st.session_state.current_tab = 2
           
           next_step, tab = get_next_step(wo_id)
           st.success(f"Work Order {wo_id} created. Next step: {next_step}")
           
           # Update inventory tracking
           c.execute("""INSERT INTO inventory 
                       (wo_id, date, status) 
                       VALUES (?, ?, ?)""",
                    (wo_id, date.strftime('%Y-%m-%d'), 'Created'))
           conn.commit()
           conn.close()

def configure_tray():
   # Initialize session states
   if 'pending_configuration' not in st.session_state:
       st.session_state.pending_configuration = False
   if 'selected_experiments' not in st.session_state:
       st.session_state.selected_experiments = []
   if 'config_initialized' not in st.session_state:
       st.session_state.config_initialized = False
   if 'current_config' not in st.session_state:
       st.session_state.current_config = None
   if 'experiment_selection' not in st.session_state:
       st.session_state.experiment_selection = []

   st.header("Tray Configuration")

   if st.session_state.pending_configuration or 'current_wo' in st.session_state:
       wo_id = st.session_state.current_wo
       conn = create_connection()
       c = conn.cursor()
       c.execute("SELECT id, customer, requester FROM work_orders WHERE id=?", (wo_id,))
       wo = c.fetchone()
       conn.close()

       if wo:
           col1, col2 = st.columns([2, 1])
           with col1:
               st.info(f"Configuring Work Order: {wo[0]} - {wo[1]} ({wo[2]})")
               
               def on_experiment_change():
                   st.session_state.config_initialized = True

               optimizer = ReagentOptimizer()
               experiments = optimizer.get_available_experiments()
               
               selected = st.multiselect(
                   "Select Experiments",
                   [f"{exp['id']}: {exp['name']}" for exp in experiments],
                   key=f"experiment_selector_{wo_id}",
                   default=st.session_state.experiment_selection,
                   on_change=on_experiment_change
               )
               st.session_state.experiment_selection = selected

               if st.button("Optimize Configuration", key=f"optimize_button_{wo_id}"):
                   if selected:
                       exp_ids = [int(exp.split(':')[0]) for exp in selected]
                       try:
                           config = optimizer.optimize_tray_configuration(exp_ids)
                           st.session_state.current_config = config
                           
                           conn = create_connection()
                           c = conn.cursor()
                           
                           c.execute("""INSERT INTO trays 
                                      (wo_id, customer, requester, date, configuration)
                                      VALUES (?, ?, ?, ?, ?)""",
                                   (wo[0], wo[1], wo[2], 
                                    datetime.now().strftime('%Y-%m-%d'), str(config)))
                           
                           c.execute("""UPDATE inventory 
                                      SET status = 'Configured'
                                      WHERE wo_id = ?""", (wo[0],))
                           conn.commit()
                           conn.close()
                           
                           next_step, tab = get_next_step(wo[0])
                           st.success(f"Configuration saved. Next step: {next_step}")
                           
                           # Reset states after successful configuration
                           st.session_state.pending_configuration = False
                           st.session_state.config_initialized = False
                           st.session_state.experiment_selection = []
                           if 'current_wo' in st.session_state:
                               del st.session_state.current_wo
                           
                       except Exception as e:
                           st.error(f"Error: {e}")
                   else:
                       st.warning("Please select at least one experiment")

           with col2:
               if st.session_state.current_config:
                   st.plotly_chart(create_tray_visualization(st.session_state.current_config))

   else:
       conn = create_connection()
       c = conn.cursor()
       c.execute("""SELECT wo.id, wo.customer, wo.requester 
                    FROM work_orders wo
                    LEFT JOIN trays t ON wo.id = t.wo_id
                    WHERE wo.status = 'Open' AND t.id IS NULL""")
       pending_wo = c.fetchall()
       
       if not pending_wo:
           st.info("No work orders pending configuration")
       else:
           st.info("Select a work order from the Work Orders tab to begin configuration")
       conn.close()

   # Search configurations section remains the same...


def create_tray_visualization(config):
    # [Previous visualization code remains the same]
    pass

def get_reagent_color(reagent_code):
    # [Previous color mapping code remains the same]
    pass

def manage_production():
    st.header("Production")
    
    conn = create_connection()
    c = conn.cursor()
    c.execute("""SELECT t.id, wo.id, wo.customer, wo.requester, t.date 
                 FROM trays t
                 JOIN work_orders wo ON t.wo_id = wo.id
                 LEFT JOIN production p ON t.id = p.tray_id
                 WHERE p.id IS NULL""")
    pending_trays = c.fetchall()
    
    if not pending_trays:
        st.info("No trays pending production")
        conn.close()
        return
        
    tray = st.selectbox("Select Tray", pending_trays,
                       format_func=lambda x: f"{x[1]} - {x[2]} - {x[3]}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Production Steps")
        production_steps = {
            "Reagent Loading": ["Volume Check", "Reagent Placement Verification"],
            "Sealing": ["Seal Integrity", "Temperature Check"],
            "Labeling": ["Label Accuracy", "Barcode Verification"],
            "QC": ["Visual Inspection", "Documentation Complete"]
        }
        
        completed_steps = {}
        for step, checks in production_steps.items():
            with st.expander(step):
                completed = True
                for check in checks:
                    if not st.checkbox(check, key=f"{tray[0]}_{check}"):
                        completed = False
                completed_steps[step] = completed
                
        if st.button("Complete Production") and all(completed_steps.values()):
            now = datetime.now().strftime('%Y-%m-%d')
            c.execute("""INSERT INTO production 
                        (tray_id, wo_id, start_date, end_date, status)
                        VALUES (?, ?, ?, ?, ?)""",
                     (tray[0], tray[1], now, now, 'Complete'))
            
            # Update inventory status
            c.execute("""UPDATE inventory 
                       SET status = 'Production Complete'
                       WHERE wo_id = ?""", (tray[1],))
            conn.commit()
            
            next_step, tab = get_next_step(tray[1])
            st.success(f"Production completed. Next step: {next_step}")

def manage_inventory():
    st.header("Inventory Tracking")
    
    conn = create_connection()
    c = conn.cursor()
    
    # Inventory status view
    st.subheader("Work Order Status")
    c.execute("""SELECT 
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
                 ORDER BY i.date DESC""")
    
    df = pd.DataFrame(c.fetchall(), 
                     columns=['Work Order', 'Customer', 'Requester', 'Date', 
                             'Status', 'Tray ID', 'Production', 'Shipping'])
    st.dataframe(df, use_container_width=True)
    
    # Reagent tracking
    st.subheader("Reagent Usage")
    if 'selected_wo' in st.session_state:
        wo = st.session_state.selected_wo
        if 'config' in st.session_state:
            config = st.session_state.config
            reagents_df = pd.DataFrame([
                {
                    'Work Order': wo[0],
                    'Customer': wo[1],
                    'Reagent': loc['reagent_code'],
                    'Location': f"LOC-{idx + 1}",
                    'Tests': loc['tests_possible']
                }
                for idx, loc in enumerate(config['tray_locations'])
                if loc
            ])
            st.dataframe(reagents_df, use_container_width=True)

def manage_shipping():
    st.header("Shipping")
    
    conn = create_connection()
    c = conn.cursor()
    c.execute("""SELECT t.id, wo.id, wo.customer, wo.requester, t.date 
                 FROM trays t
                 JOIN work_orders wo ON t.wo_id = wo.id
                 JOIN production p ON t.id = p.tray_id
                 LEFT JOIN shipping s ON t.id = s.tray_id
                 WHERE p.status = 'Complete' AND s.id IS NULL""")
    ready_trays = c.fetchall()
    
    if not ready_trays:
        st.info("No trays ready for shipping")
        conn.close()
        return
        
    with st.form("shipping"):
        tray = st.selectbox("Select Tray", ready_trays,
                           format_func=lambda x: f"{x[1]} - {x[2]} - {x[3]}")
        cols = st.columns([2, 2])
        tracking = cols[0].text_input("Tracking Number")
        ship_date = cols[1].date_input("Ship Date")
        
        if st.form_submit_button("Process Shipment") and tracking:
            c.execute("""INSERT INTO shipping 
                        (tray_id, wo_id, customer, requester, tracking_number, ship_date)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (tray[0], tray[1], tray[2], tray[3], tracking, 
                      ship_date.strftime('%Y-%m-%d')))
            
            # Update work order status
            c.execute("UPDATE work_orders SET status = 'Complete' WHERE id = ?", 
                     (tray[1],))
            
            # Update inventory status
            c.execute("UPDATE inventory SET status = 'Shipped' WHERE wo_id = ?", 
                     (tray[1],))
            conn.commit()
            st.success(f"Shipment processed: {tracking}")
    
    # Shipping history
    st.subheader("Shipping History")
    c.execute("""SELECT wo.id, wo.customer, wo.requester, 
                 s.tracking_number, s.ship_date
                 FROM shipping s
                 JOIN work_orders wo ON s.wo_id = wo.id
                 ORDER BY s.ship_date DESC""")
    
    df = pd.DataFrame(c.fetchall(), 
                     columns=['Work Order', 'Customer', 'Requester',
                             'Tracking Number', 'Ship Date'])
    st.dataframe(df, use_container_width=True)
    conn.close()

def show_dashboard():
    st.header("Dashboard")
    
    conn = create_connection()
    c = conn.cursor()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    c.execute("SELECT COUNT(*) FROM work_orders WHERE status='Open'")
    col1.metric("Open Work Orders", c.fetchone()[0])
    
    c.execute("SELECT COUNT(*) FROM trays WHERE date=?", 
             (datetime.now().strftime('%Y-%m-%d'),))
    col2.metric("Today's Trays", c.fetchone()[0])
    
    c.execute("SELECT COUNT(*) FROM production WHERE end_date=?", 
             (datetime.now().strftime('%Y-%m-%d'),))
    col3.metric("Completed Production", c.fetchone()[0])
    
    c.execute("SELECT COUNT(*) FROM shipping WHERE ship_date=?", 
             (datetime.now().strftime('%Y-%m-%d'),))
    col4.metric("Today's Shipments", c.fetchone()[0])

    # Activity charts
    st.subheader("Activity Overview")
    
    # Work order trend
    c.execute("""SELECT date, COUNT(*) FROM work_orders 
                 WHERE date >= date('now', '-30 days')
                 GROUP BY date ORDER BY date""")
    wo_data = pd.DataFrame(c.fetchall(), columns=['date', 'count'])
    
    # Production trend
    c.execute("""SELECT end_date, COUNT(*) FROM production 
                 WHERE end_date >= date('now', '-30 days')
                 GROUP BY end_date ORDER BY end_date""")
    prod_data = pd.DataFrame(c.fetchall(), columns=['date', 'count'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=wo_data['date'], y=wo_data['count'], 
                            name='Work Orders', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=prod_data['date'], y=prod_data['count'], 
                            name='Production', mode='lines+markers'))
    fig.update_layout(title='30-Day Activity', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    c.execute("""SELECT 
                 wo.id as wo_id,
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
                 ORDER BY date DESC LIMIT 10""")
    
    activity_df = pd.DataFrame(c.fetchall(), 
                             columns=['Work Order', 'Customer', 'Requester', 
                                     'Status', 'Date'])
    st.dataframe(activity_df, use_container_width=True)
    conn.close()

def main():
   st.title("🧪 Reagent LIMS")
   
   # CSS styling
   st.markdown("""
       <style>
       .stTabs [data-baseweb="tab-list"] {
           gap: 2px;
       }
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
       .stButton>button:hover {
           background-color: #45a049;
       }
       .reportview-container .main .block-container {
           padding-top: 1rem;
       }
       .stDataFrame {
           background-color: white;
           padding: 1rem;
           border-radius: 4px;
           box-shadow: 0 2px 4px rgba(0,0,0,0.1);
       }
       .stPlotlyChart {
           background-color: white;
           padding: 1rem;
           border-radius: 4px;
           box-shadow: 0 2px 4px rgba(0,0,0,0.1);
       }
       </style>
   """, unsafe_allow_html=True)
   
   # Initialize session state for tab management
   if 'current_tab' not in st.session_state:
       st.session_state.current_tab = 0
   
   # Tab navigation
   tabs = st.tabs([
       "Dashboard", 
       "Work Orders", 
       "Tray Configuration", 
       "Inventory", 
       "Production", 
       "Shipping",
       "Search & Reports"
   ])
   
   with tabs[0]: show_dashboard()
   with tabs[1]: manage_work_orders()
   with tabs[2]: configure_tray()
   with tabs[3]: manage_inventory()
   with tabs[4]: manage_production()
   with tabs[5]: manage_shipping()
   with tabs[6]: search_and_reports()

if __name__ == "__main__":
   main()

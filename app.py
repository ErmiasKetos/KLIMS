import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reagent_optimizer import ReagentOptimizer
import sqlite3
from datetime import datetime

# Page config and database setup
st.set_page_config(page_title="Reagent LIMS", page_icon="🧪", layout="wide")
conn = sqlite3.connect('reagent_lims.db')
c = conn.cursor()

# Create necessary tables
def setup_database():
    c.execute('''CREATE TABLE IF NOT EXISTS work_orders
                 (id INTEGER PRIMARY KEY, customer TEXT, date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trays
                 (id INTEGER PRIMARY KEY, wo_id INTEGER, customer TEXT, date TEXT, configuration TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS production
                 (id INTEGER PRIMARY KEY, tray_id INTEGER, start_date TEXT, end_date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shipping
                 (id INTEGER PRIMARY KEY, tray_id INTEGER, tracking_number TEXT, ship_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY, reagent TEXT, batch TEXT, quantity INTEGER, date TEXT)''')
    conn.commit()

def get_reagent_color(reagent_code):
    color_map = {
        'gray': ['KR1E', 'KR1S', 'KR2S', 'KR3E', 'KR3S', 'KR4E', 'KR4S', 'KR5E', 'KR5S', 
                 'KR6E1', 'KR6E2', 'KR6E3', 'KR13E1', 'KR13S', 'KR14E', 'KR14S', 'KR15E', 'KR15S'],
        'violet': ['KR7E1', 'KR7E2', 'KR8E1', 'KR8E2', 'KR19E1', 'KR19E2', 'KR19E3', 'KR20E',
                  'KR36E1', 'KR36E2', 'KR40E1', 'KR40E2'],
        'green': ['KR9E1', 'KR9E2', 'KR17E1', 'KR17E2', 'KR17E3', 'KR28E1', 'KR28E2', 'KR28E3'],
        'orange': ['KR10E1', 'KR10E2', 'KR10E3', 'KR12E1', 'KR12E2', 'KR12E3', 'KR18E1',
                  'KR18E2', 'KR22E1', 'KR27E1', 'KR27E2', 'KR42E1', 'KR42E2'],
        'white': ['KR11E', 'KR21E1'],
        'blue': ['KR16E1', 'KR16E2', 'KR16E3', 'KR16E4', 'KR30E1', 'KR30E2', 'KR30E3',
                'KR31E1', 'KR31E2', 'KR34E1', 'KR34E2'],
        'red': ['KR29E1', 'KR29E2', 'KR29E3'],
        'yellow': ['KR35E1', 'KR35E2']
    }
    return next((color for color, reagents in color_map.items() 
                if any(reagent_code.startswith(r) for r in reagents)), 'lightgray')

def create_tray_visualization(config):
    locations = config["tray_locations"]
    fig = go.Figure()

    for i, loc in enumerate(locations):
        row, col = i // 4, i % 4
        color = get_reagent_color(loc['reagent_code']) if loc else 'lightgray'
        opacity = 0.8 if loc else 0.2

        # Add cell shape
        fig.add_trace(go.Scatter(
            x=[col, col+1, col+1, col, col],
            y=[row, row, row+1, row+1, row],
            fill="toself",
            fillcolor=color,
            opacity=opacity,
            line=dict(color="black", width=1),
            mode="lines",
            name=f"LOC-{i+1}",
            text=f"LOC-{i+1}<br>{loc['reagent_code'] if loc else 'Empty'}<br>"
                 f"Tests: {loc['tests_possible'] if loc else 'N/A'}<br>"
                 f"Exp: #{loc['experiment'] if loc else 'N/A'}",
            hoverinfo="text"
        ))

        # Add text annotation
        fig.add_annotation(
            x=(col + 0.5),
            y=(row + 0.5),
            text=f"<b>LOC-{i+1}</b><br>{'<b>' + loc['reagent_code'] if loc else 'Empty</b>'}<br>"
                 f"Tests: {loc['tests_possible'] if loc else 'N/A'}<br>"
                 f"Exp: #{loc['experiment'] if loc else 'N/A'}",
            showarrow=False,
            font=dict(size=10),
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

def display_metrics():
    c.execute("SELECT COUNT(*) FROM work_orders WHERE status='Open'")
    open_wo = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trays WHERE date=?", (datetime.now().strftime('%Y-%m-%d'),))
    trays_today = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM shipping WHERE ship_date=?", (datetime.now().strftime('%Y-%m-%d'),))
    shipments_today = c.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Open Work Orders", open_wo)
    col2.metric("Trays Created Today", trays_today)
    col3.metric("Shipments Today", shipments_today)

def show_dashboard():
    st.header("Dashboard")
    display_metrics()
    
    # Activity charts
    c.execute("SELECT date, COUNT(*) FROM work_orders GROUP BY date ORDER BY date LIMIT 30")
    wo_data = pd.DataFrame(c.fetchall(), columns=['date', 'count'])
    c.execute("SELECT date, COUNT(*) FROM trays GROUP BY date ORDER BY date LIMIT 30")
    tray_data = pd.DataFrame(c.fetchall(), columns=['date', 'count'])
    
    if not wo_data.empty and not tray_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=wo_data['date'], y=wo_data['count'], name='Work Orders'))
        fig.add_trace(go.Scatter(x=tray_data['date'], y=tray_data['count'], name='Trays'))
        fig.update_layout(title='30-Day Activity', height=400)
        st.plotly_chart(fig, use_container_width=True)

def manage_work_orders():
    st.header("Work Orders")
    
    with st.form("new_work_order"):
        cols = st.columns([2, 1, 1])
        customer = cols[0].text_input("Customer")
        date = cols[1].date_input("Date")
        cols[2].write("")  # Spacing
        submitted = cols[2].form_submit_button("Create Work Order")
        
        if submitted and customer:
            c.execute("INSERT INTO work_orders (customer, date, status) VALUES (?, ?, ?)",
                     (customer, date.strftime('%Y-%m-%d'), 'Open'))
            conn.commit()
            st.success(f"Work Order created: {customer}")

def configure_tray():
    st.header("Tray Configuration")
    
    c.execute("SELECT id, customer, date FROM work_orders WHERE status='Open'")
    work_orders = c.fetchall()
    if not work_orders:
        st.warning("Create a work order first")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        wo = st.selectbox("Work Order", work_orders, 
                         format_func=lambda x: f"{x[1]} - {x[2]}")
        
        optimizer = ReagentOptimizer()
        experiments = optimizer.get_available_experiments()
        selected = st.multiselect("Experiments", 
                                 [f"{exp['id']}: {exp['name']}" for exp in experiments])
        
        if st.button("Optimize") and selected:
            exp_ids = [int(exp.split(':')[0]) for exp in selected]
            try:
                config = optimizer.optimize_tray_configuration(exp_ids)
                st.session_state.config = config
                
                # Save configuration
                c.execute("""INSERT INTO trays (wo_id, customer, date, configuration) 
                           VALUES (?, ?, ?, ?)""",
                        (wo[0], wo[1], datetime.now().strftime('%Y-%m-%d'), str(config)))
                conn.commit()
                st.success("Configuration saved")
            except Exception as e:
                st.error(f"Error: {e}")

    if 'config' in st.session_state:
        with col2:
            st.plotly_chart(create_tray_visualization(st.session_state.config))

def manage_inventory():
    st.header("Inventory")
    
    cols = st.columns([2, 1, 1, 1])
    with cols[0].form("inventory"):
        reagent = st.text_input("Reagent")
        batch = st.text_input("Batch")
        quantity = st.number_input("Quantity", min_value=1)
        if st.form_submit_button("Add Stock"):
            c.execute("""INSERT INTO inventory (reagent, batch, quantity, date)
                        VALUES (?, ?, ?, ?)""",
                     (reagent, batch, quantity, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            st.success(f"Added {quantity} of {reagent}")

    # Show inventory table
    c.execute("SELECT reagent, batch, SUM(quantity) as total FROM inventory GROUP BY reagent, batch")
    inv_data = pd.DataFrame(c.fetchall(), columns=['Reagent', 'Batch', 'Quantity'])
    st.dataframe(inv_data)

def manage_production():
    st.header("Production")
    
    c.execute("""SELECT t.id, t.customer, t.date FROM trays t
                 LEFT JOIN production p ON t.id = p.tray_id
                 WHERE p.id IS NULL""")
    pending_trays = c.fetchall()
    
    if not pending_trays:
        st.info("No trays pending production")
        return
        
    tray = st.selectbox("Select Tray", pending_trays,
                       format_func=lambda x: f"{x[1]} - {x[2]}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Production Steps")
        steps = ["Reagent Loading", "Sealing", "Labeling", "QC Check"]
        completed = []
        for step in steps:
            if st.checkbox(step):
                completed.append(step)
                
        if st.button("Complete Production") and len(completed) == len(steps):
            c.execute("""INSERT INTO production (tray_id, start_date, end_date, status)
                        VALUES (?, ?, ?, ?)""",
                     (tray[0], datetime.now().strftime('%Y-%m-%d'),
                      datetime.now().strftime('%Y-%m-%d'), 'Complete'))
            conn.commit()
            st.success("Production completed")

def manage_shipping():
    st.header("Shipping")
    
    c.execute("""SELECT t.id, t.customer, t.date FROM trays t
                 INNER JOIN production p ON t.id = p.tray_id
                 LEFT JOIN shipping s ON t.id = s.tray_id
                 WHERE p.status = 'Complete' AND s.id IS NULL""")
    ready_trays = c.fetchall()
    
    if not ready_trays:
        st.info("No trays ready for shipping")
        return
        
    cols = st.columns([2, 2, 1])
    with cols[0].form("shipping"):
        tray = st.selectbox("Tray", ready_trays,
                          format_func=lambda x: f"{x[1]} - {x[2]}")
        tracking = st.text_input("Tracking Number")
        if st.form_submit_button("Ship") and tracking:
            c.execute("""INSERT INTO shipping (tray_id, tracking_number, ship_date)
                        VALUES (?, ?, ?)""",
                     (tray[0], tracking, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            st.success(f"Shipped: {tracking}")

def main():
    st.title("🧪 Reagent LIMS")
    setup_database()
    
    tabs = st.tabs(["Dashboard", "Work Orders", "Tray Configuration", 
                    "Inventory", "Production", "Shipping"])
    
    with tabs[0]: show_dashboard()
    with tabs[1]: manage_work_orders()
    with tabs[2]: configure_tray()
    with tabs[3]: manage_inventory()
    with tabs[4]: manage_production()
    with tabs[5]: manage_shipping()

if __name__ == "__main__":
    main()

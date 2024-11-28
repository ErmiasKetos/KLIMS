import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reagent_optimizer import ReagentOptimizer
import sqlite3
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Reagent Tray LIMS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS (unchanged)
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

# Database setup
conn = sqlite3.connect('reagent_tray_lims.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS work_orders
             (id TEXT PRIMARY KEY, customer TEXT, requester TEXT, date TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tray_configurations
             (id INTEGER PRIMARY KEY, work_order_id TEXT, configuration TEXT)''')
conn.commit()

def get_reagent_color(reagent_code):
    # (Unchanged function)
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

def create_tray_visualization(config):
    # (Unchanged function)
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
    # (Unchanged function)
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Tray Configuration")
        fig = create_tray_visualization(config)
        st.plotly_chart(fig, use_container_width=True)

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

def reset_app():
    """Clears all session state variables to reset the app."""
    for key in list(st.session_state.keys()):
        if key.startswith('exp_'):
            st.session_state[key] = False
        else:
            del st.session_state[key]

def main():
    st.title("🧪 Reagent Tray LIMS")
    
    tabs = st.tabs(["Work Orders", "Tray Configuration", "Shipping"])

    with tabs[0]:
        work_order_management()

    with tabs[1]:
        tray_configuration()

    with tabs[2]:
        shipping()

def work_order_management():
    st.header("Work Order Management")

    # Form for creating new work orders
    with st.form("new_work_order"):
        customer = st.text_input("Customer Name")
        requester = st.text_input("Requester Name")
        date = st.date_input("Order Date")
        if st.form_submit_button("Create Work Order"):
            # Generate work order ID
            c.execute("SELECT COUNT(*) FROM work_orders")
            count = c.fetchone()[0]
            wo_id = f"WO-{date.strftime('%y-%m')}-{(count+1):04d}"
            
            # Insert new work order
            c.execute("INSERT INTO work_orders (id, customer, requester, date, status) VALUES (?, ?, ?, ?, ?)",
                      (wo_id, customer, requester, date.strftime('%Y-%m-%d'), 'Created'))
            conn.commit()
            st.success(f"Work Order {wo_id} created successfully. Next step: Tray Configuration")

    # Display existing work orders
    c.execute("SELECT * FROM work_orders ORDER BY date DESC")
    work_orders = c.fetchall()
    if work_orders:
        df = pd.DataFrame(work_orders, columns=['ID', 'Customer', 'Requester', 'Date', 'Status'])
        st.dataframe(df)
    else:
        st.info("No work orders found. Create a new work order to get started.")

def tray_configuration():
    st.header("Tray Configuration")

    # Work order selection
    c.execute("SELECT id, customer FROM work_orders WHERE status='Created'")
    open_work_orders = c.fetchall()
    if not open_work_orders:
        st.warning("No open work orders. Please create a work order first.")
        return

    selected_wo = st.selectbox("Select Work Order", options=open_work_orders, format_func=lambda x: f"{x[0]} - {x[1]}")

    optimizer = ReagentOptimizer()
    experiments = optimizer.get_available_experiments()

    # Experiment selection
    selected_experiments = st.multiselect("Select experiments", options=[f"{exp['id']}: {exp['name']}" for exp in experiments])
    selected_ids = [int(exp.split(':')[0]) for exp in selected_experiments]

    if st.button("Optimize Configuration"):
        if not selected_ids:
            st.error("Please select at least one experiment")
        else:
            try:
                with st.spinner("Optimizing tray configuration..."):
                    config = optimizer.optimize_tray_configuration(selected_ids)
                
                # Save configuration to database
                c.execute("INSERT INTO tray_configurations (work_order_id, configuration) VALUES (?, ?)",
                          (selected_wo[0], str(config)))
                conn.commit()

                # Update work order status
                c.execute("UPDATE work_orders SET status = 'Configured' WHERE id = ?", (selected_wo[0],))
                conn.commit()

                st.session_state.config = config
                st.success("Configuration optimized and saved successfully! Next step: Shipping")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Display saved configuration for the selected work order
    c.execute("SELECT configuration FROM tray_configurations WHERE work_order_id = ?", (selected_wo[0],))
    saved_config = c.fetchone()
    if saved_config:
        st.subheader("Saved Configuration")
        config = eval(saved_config[0])  # Convert string representation back to dictionary
        display_results(config, selected_ids)

def shipping():
    st.header("Shipping")

    # Display work orders ready for shipping
    c.execute("SELECT id, customer FROM work_orders WHERE status='Configured'")
    ready_for_shipping = c.fetchall()
    if not ready_for_shipping:
        st.warning("No work orders ready for shipping.")
        return

    selected_wo = st.selectbox("Select Work Order for Shipping", options=ready_for_shipping, format_func=lambda x: f"{x[0]} - {x[1]}")

    if st.button("Mark as Shipped"):
        # Update work order status
        c.execute("UPDATE work_orders SET status = 'Shipped' WHERE id = ?", (selected_wo[0],))
        conn.commit()
        st.success(f"Work Order {selected_wo[0]} marked as shipped. Process complete.")

    # Display all shipped work orders
    c.execute("SELECT * FROM work_orders WHERE status='Shipped' ORDER BY date DESC")
    shipped_orders = c.fetchall()
    if shipped_orders:
        df = pd.DataFrame(shipped_orders, columns=['ID', 'Customer', 'Requester', 'Date', 'Status'])
        st.subheader("Shipped Work Orders")
        st.dataframe(df)

if __name__ == "__main__":
    main()

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from config.settings import CURRENT_MODE, ExecutionMode, SERIAL_PORT, BAUD_RATE
from telemetry.telemetry_manager import TelemetryManager
from storage.csv_logger import CSVLogger
from communication.serial_receiver import SerialReceiver
from communication.command_sender import CommandSender
from simulation.telemetry_simulator import TelemetrySimulator

# Must be the first Streamlit command
st.set_page_config(page_title="ASTRA SENSE NEXSUS", layout="wide", initial_sidebar_state="expanded")

def inject_custom_css():
    st.markdown("""
        <style>
            /* Primary color accents and typography */
            :root {
                --primary: #003366;
                --accent: #E67E22;
            }
            .stApp {
                background-color: #ffffff;
                color: #333333;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            .mode-banner {
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 5px;
                color: white;
                font-weight: bold;
                text-align: center;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            .mode-real {
                background-color: #003366;
            }
            .mode-sim {
                background-color: #E67E22;
            }
            .metric-card {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #003366;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                margin-bottom: 15px;
            }
            .metric-title {
                font-size: 0.9rem;
                color: #666;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: bold;
                color: #003366;
            }
            .stSidebar {
                background-color: #f1f3f5;
            }
        </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_backend():
    """Process-level singleton for all backend components."""
    manager = TelemetryManager()
    logger = CSVLogger(mode=CURRENT_MODE)
    logger.start()
    
    if CURRENT_MODE == ExecutionMode.SIMULATION:
        simulator = TelemetrySimulator(manager=manager, logger=logger)
        # Note: We do not start the simulator automatically, 
        # it is controlled via the Commands page.
        receiver = None
        command_sender = CommandSender(manager=manager, receiver=None)
        return {
            "manager": manager,
            "logger": logger,
            "receiver": None,
            "simulator": simulator,
            "command_sender": command_sender
        }
    else:
        receiver = SerialReceiver(port=SERIAL_PORT, baud_rate=BAUD_RATE, manager=manager, logger=logger)
        receiver.start()
        command_sender = CommandSender(manager=manager, receiver=receiver)
        return {
            "manager": manager,
            "logger": logger,
            "receiver": receiver,
            "simulator": None,
            "command_sender": command_sender
        }

def display_mode_banner(manager: TelemetryManager):
    status = manager.get_status()
    if CURRENT_MODE == ExecutionMode.REAL:
        st.markdown(f'<div class="mode-banner mode-real">MODE: REAL &nbsp;|&nbsp; RADIO: {status["connection_text"]} &nbsp;|&nbsp; TLM RATE: {status["rate_hz"]:.1f} Hz</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-banner mode-sim">MODE: SIMULATION</div>', unsafe_allow_html=True)

def main():
    inject_custom_css()
    
    # Init backend singleton
    backend = init_backend()
    manager = backend["manager"]
    
    # Auto-refresh at 2Hz (every 500ms)
    # limit is 0 meaning it runs forever
    st_autorefresh(interval=500, limit=None, key="data_refresh")
    
    # Sidebar Navigation
    st.sidebar.title("ASTRA SENSE NEXSUS")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Live Plots", "Commands", "Diagnostics"])
    
    # Display top banner
    display_mode_banner(manager)
    
    # Route to pages
    if page == "Dashboard":
        from ui.dashboard import render_dashboard
        render_dashboard(backend)
    elif page == "Live Plots":
        from ui.plots import render_plots
        render_plots(backend)
    elif page == "Commands":
        from ui.commands import render_commands
        render_commands(backend)
    elif page == "Diagnostics":
        from ui.diagnostics import render_diagnostics
        render_diagnostics(backend)

if __name__ == "__main__":
    main()

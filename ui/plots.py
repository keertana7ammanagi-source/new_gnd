import streamlit as st
import pandas as pd
import plotly.express as px
from config.telemetry_schema import TELEMETRY_SCHEMA

def render_plots(backend):
    manager = backend["manager"]
    
    st.header("Live Telemetry Plots")
    
    # Filter fields that are plot-capable (numeric)
    plot_fields = [f.name for f in TELEMETRY_SCHEMA if f.plot and f.name != "TIMESTAMP" and f.name != "PACKET_COUNT"]
    
    # Provide a multiselect so users can select what to plot
    # Store selection in session_state so it persists across autorefreshes
    selected_fields = st.multiselect(
        "Select fields to plot",
        options=plot_fields,
        default=st.session_state.get("selected_plot_fields", ["ALTITUDE"]),
        key="selected_plot_fields_widget"
    )
    
    # Sync widget state to persistent session state
    st.session_state["selected_plot_fields"] = selected_fields
    
    history = manager.get_history()
    if not history:
        st.info("No telemetry data available to plot yet.")
        return

    if not selected_fields:
        st.warning("Please select at least one field to plot.")
        return

    # Convert bounded history to DataFrame
    df = pd.DataFrame(history)
    
    # Filter by time window (last N packets, configurable in UI)
    window_size = st.slider("Time Window (Packets)", min_value=50, max_value=5000, value=1000, step=50)
    df = df.tail(window_size)
    
    if "TIMESTAMP" not in df.columns:
        st.error("TIMESTAMP field missing from telemetry data.")
        return
        
    for field in selected_fields:
        if field in df.columns:
            fig = px.line(
                df, 
                x="TIMESTAMP", 
                y=field, 
                title=f"{field} vs Mission Time",
                template="plotly_white"
            )
            # Apply styling
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color='#003366'),
                xaxis_title="Mission Time (s)"
            )
            fig.update_traces(line_color='#E67E22')
            st.plotly_chart(fig, use_container_width=True)

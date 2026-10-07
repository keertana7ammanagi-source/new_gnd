import streamlit as st
import pandas as pd
from config.settings import CURRENT_MODE, SERIAL_PORT, BAUD_RATE
from config.telemetry_schema import SCHEMA_VERSION, EXPECTED_FIELD_COUNT

def render_diagnostics(backend):
    manager = backend["manager"]
    logger = backend["logger"]
    
    st.header("Telemetry & Diagnostics")

    # High-level System Info
    st.subheader("System Info")
    info_col1, info_col2, info_col3 = st.columns(3)
    
    status = manager.get_status()
    
    with info_col1:
        st.metric("Execution Mode", CURRENT_MODE.value)
        st.metric("Connection", status["connection_text"])
        st.metric("Telemetry Rate", f"{status['rate_hz']:.1f} Hz")
        
    with info_col2:
        st.metric("Packets Received", status["total_received"])
        st.metric("Packets Lost", status["total_lost"])
        st.metric("Invalid Packets", status["total_invalid"])
        
    with info_col3:
        st.metric("Duplicate Packets", status["total_duplicates"])
        st.metric("Schema Version", SCHEMA_VERSION)
        st.metric("Expected Field Count", EXPECTED_FIELD_COUNT)
        
    st.markdown("---")
    
    st.subheader("CSV Logging")
    st.code(f"Path: {logger.filepath}\nError Log: {logger.error_filepath}", language="text")

    st.markdown("---")
    
    st.subheader("Latest Raw Packet")
    raw_packet = manager.get_latest_raw()
    if raw_packet:
        field_count = len(raw_packet.split(','))
        st.caption(f"Length: {field_count} fields")
        st.code(raw_packet, language="text")
    else:
        st.info("No packets received yet.")

    st.markdown("---")
    
    st.subheader("Latest Parsed Telemetry")
    latest = manager.get_latest()
    if latest:
        # Show as an interactive dataframe/table
        df = pd.DataFrame([latest])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No valid telemetry parsed yet.")

    st.markdown("---")
    
    st.subheader("Warnings & Errors Log")
    warnings = manager.warnings
    if warnings:
        for w in reversed(warnings):
            st.warning(w)
    else:
        st.success("No warnings or errors.")

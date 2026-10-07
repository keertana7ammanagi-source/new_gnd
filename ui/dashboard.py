import streamlit as st
from config.telemetry_schema import SCHEMA_BY_NAME

def metric_card(title, value, unit=""):
    """Helper to render a styled metric card."""
    if value is None:
        display_val = "N/A"
    else:
        display_val = f"{value} {unit}".strip()
        
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{display_val}</div>
        </div>
    """, unsafe_allow_html=True)

def format_val(field_name: str, raw_val) -> str:
    if raw_val is None:
        return "N/A"
    field = SCHEMA_BY_NAME.get(field_name)
    if not field:
        return str(raw_val)
    if isinstance(raw_val, float):
        return f"{raw_val:.{field.precision}f}"
    return str(raw_val)

def render_dashboard(backend):
    manager = backend["manager"]
    status = manager.get_status()
    latest = manager.get_latest()

    st.header("Flight Dashboard")

    if not status["is_connected"] or latest is None:
        st.warning("⚠️ STALE / NO RECENT TELEMETRY")
        if latest is None:
            st.info("Waiting for first valid packet...")
            return

    # Primary Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Altitude", format_val("ALTITUDE", latest.get("ALTITUDE")), SCHEMA_BY_NAME["ALTITUDE"].unit)
    with col2:
        metric_card("Vertical Speed", format_val("VERTICAL_SPEED", latest.get("VERTICAL_SPEED")), SCHEMA_BY_NAME["VERTICAL_SPEED"].unit)
    with col3:
        metric_card("Voltage", format_val("VOLTAGE", latest.get("VOLTAGE")), SCHEMA_BY_NAME["VOLTAGE"].unit)
    with col4:
        metric_card("Flight State", latest.get("FLIGHT_SOFTWARE_STATE", "UNKNOWN"))

    st.markdown("---")

    # Secondary Rows
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("GNSS")
        g1, g2, g3 = st.columns(3)
        with g1:
            st.metric("Fix", latest.get("GNSS_FIX", "N/A"))
            st.metric("Sats", latest.get("GNSS_SATS", "N/A"))
        with g2:
            st.metric("Lat", format_val("GNSS_LATITUDE", latest.get("GNSS_LATITUDE")))
            st.metric("Lon", format_val("GNSS_LONGITUDE", latest.get("GNSS_LONGITUDE")))
        with g3:
            st.metric("GNSS Alt", format_val("GNSS_ALTITUDE", latest.get("GNSS_ALTITUDE")) + " m")
            st.metric("Speed", format_val("GNSS_GROUND_SPEED", latest.get("GNSS_GROUND_SPEED")) + " m/s")

        st.subheader("Environment")
        e1, e2 = st.columns(2)
        with e1:
            st.metric("Pressure", format_val("PRESSURE", latest.get("PRESSURE")) + " Pa")
            st.metric("Temp", format_val("TEMP", latest.get("TEMP")) + " °C")
        with e2:
            st.metric("Humidity", format_val("HUMIDITY", latest.get("HUMIDITY")) + " %RH")
            st.metric("UV Index", format_val("UV_INDEX", latest.get("UV_INDEX")))

    with col_b:
        st.subheader("Attitude")
        att1, att2, att3 = st.columns(3)
        with att1:
            st.metric("Roll", format_val("ROLL", latest.get("ROLL")) + " °")
        with att2:
            st.metric("Pitch", format_val("PITCH", latest.get("PITCH")) + " °")
        with att3:
            st.metric("Yaw", format_val("YAW", latest.get("YAW")) + " °")

        st.subheader("Power & Recovery")
        pr1, pr2 = st.columns(2)
        with pr1:
            st.metric("Current", format_val("CURRENT", latest.get("CURRENT")) + " A")
            st.metric("Power", format_val("POWER", latest.get("POWER")) + " W")
        with pr2:
            st.metric("Rel Altitude", format_val("REL_ALTITUDE", latest.get("REL_ALTITUDE")) + " m")
            st.metric("Hall RPM", format_val("HALL_RPM", latest.get("HALL_RPM")) + " RPM")

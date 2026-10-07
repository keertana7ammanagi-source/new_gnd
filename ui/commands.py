import streamlit as st
from config.settings import ExecutionMode, CURRENT_MODE
from config.commands import CommandState

def render_commands(backend):
    manager = backend["manager"]
    sender = backend["command_sender"]
    simulator = backend["simulator"]
    
    st.header("Ground Station Commands")

    st.subheader("Telemetry Control")
    col_tlm, col_tlm_status = st.columns([1, 2])
    with col_tlm:
        if st.button("START TELEMETRY"):
            if not sender.send_command("START_TELEMETRY"):
                st.toast("Failed to send START_TELEMETRY", icon="❌")
            else:
                st.toast("START_TELEMETRY command sent.", icon="✅")
    with col_tlm_status:
        state = manager.get_commands().get("START_TELEMETRY").state
        payload = manager.get_commands().get("START_TELEMETRY").payload
        if payload is None:
            st.error("Status: NOT CONFIGURED (No Wire String)")
        else:
            st.info(f"Status: {state.value}")

    st.markdown("---")
    
    st.subheader("Launch Pad Calibration")
    
    cal_cmds = [
        ("CALIBRATE GYRO", "CALIBRATE_GYRO"),
        ("ZERO BAROMETRIC ALTITUDE", "ZERO_BAROMETRIC_ALTITUDE"),
        ("ZERO ACCELEROMETER", "ZERO_ACCELEROMETER")
    ]
    
    for label, cmd_id in cal_cmds:
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button(label):
                if not sender.send_command(cmd_id):
                    st.toast(f"Failed to send {label}", icon="❌")
                else:
                    st.toast(f"{label} command sent.", icon="✅")
        with c2:
            state = manager.get_commands().get(cmd_id).state
            payload = manager.get_commands().get(cmd_id).payload
            if payload is None:
                st.error("Status: NOT CONFIGURED")
            else:
                st.info(f"Status: {state.value}")

    # Simulation Controls (Only in SIMULATION mode)
    if CURRENT_MODE == ExecutionMode.SIMULATION and simulator is not None:
        st.markdown("---")
        st.subheader("🔧 Simulation Controls")
        
        sim_c1, sim_c2, sim_c3 = st.columns(3)
        with sim_c1:
            if st.button("Start Simulation", type="primary"):
                simulator.start()
        with sim_c2:
            if st.button("Stop Simulation"):
                simulator.stop()
        with sim_c3:
            if st.button("Reset Simulation"):
                simulator.stop()
                simulator.reset()
                
        st.markdown("**Fault Injection**")
        faults = simulator.faults
        f_cols = st.columns(4)
        
        # We manually render toggles for faults to update them
        idx = 0
        for f_key in faults.keys():
            with f_cols[idx % 4]:
                faults[f_key] = st.checkbox(f_key, value=faults[f_key], key=f"fault_{f_key}")
            idx += 1

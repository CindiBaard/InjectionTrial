import streamlit as st
import pandas as pd
from datetime import datetime

# Set page to wide mode to accommodate multiple columns
st.set_page_config(layout="wide", page_title="Injection Trial Tracker")

st.title("Injection Trial Data Entry")
st.markdown("---")

# Use a form to group all data entry fields
with st.form("injection_trial_form", clear_on_submit=True):
    
    # ROW 1: Identity & Reference
    col1, col2, col3 = st.columns(3)
    with col1:
        date = st.date_input("Trial Date", datetime.now())
        job_no = st.text_input("Job Number")
    with col2:
        machine = st.text_input("Machine ID / Name")
        operator = st.text_input("Operator")
    with col3:
        customer = st.text_input("Customer Name")
        part_no = st.text_input("Part Number / Description")

    st.subheader("Material & Masterbatch")
    # ROW 2: Material Specs
    col4, col5, col6 = st.columns(3)
    with col4:
        mat_grade = st.text_input("Material Grade")
    with col5:
        mb_code = st.text_input("Masterbatch Code")
    with col6:
        mb_ratio = st.number_input("MB Ratio (%)", format="%.2f", step=0.01)

    st.subheader("Machine Process Parameters")
    # ROW 3: Temperatures (Zone based)
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        zone_1 = st.number_input("Zone 1 Temp (°C)", step=1)
    with t2:
        zone_2 = st.number_input("Zone 2 Temp (°C)", step=1)
    with t3:
        zone_3 = st.number_input("Zone 3 Temp (°C)", step=1)
    with t4:
        nozzle_temp = st.number_input("Nozzle Temp (°C)", step=1)

    # ROW 4: Pressures & Times
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        inj_press = st.number_input("Inj. Pressure (bar)", step=1)
    with p2:
        hold_press = st.number_input("Hold Pressure (bar)", step=1)
    with p3:
        cycle_time = st.number_input("Cycle Time (s)", format="%.2f", step=0.1)
    with p4:
        cool_time = st.number_input("Cooling Time (s)", format="%.2f", step=0.1)

    st.subheader("Trial Observations")
    comments = st.text_area("Notes (e.g., Short shots, flashing, dimensions)")

    # Submission logic
    submit_button = st.form_submit_button("Record Trial Data")

if submit_button:
    # Constructing a data record that matches your Excel schema
    new_entry = {
        "Date": [date],
        "Job No": [job_no],
        "Machine": [machine],
        "Material": [mat_grade],
        "MB Code": [mb_code],
        "Cycle Time": [cycle_time],
        "Comments": [comments]
    }
    
    # Create DataFrame for processing
    df_new = pd.DataFrame(new_entry)
    
    # Confirmation for user
    st.success(f"Data for Job {job_no} has been recorded locally.")
    st.dataframe(df_new)
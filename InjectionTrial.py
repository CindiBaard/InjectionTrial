import streamlit as st
import pandas as pd

st.title("Injection Trial Data Entry")

# Use a form to group the inputs and prevent the app from 
# refreshing after every single character typed.
with st.form("trial_form", clear_on_submit=True):
    
    # Section 1: General Info
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date")
        machine = st.text_input("Machine")
    with col2:
        operator = st.text_input("Operator")
        mold_name = st.text_input("Mold Name / Part Number")

    st.divider()

    # Section 2: Material & Masterbatch
    st.subheader("Material Information")
    c3, c4, c5 = st.columns(3)
    with c3:
        material = st.text_input("Material Type")
    with c4:
        mb_code = st.text_input("Masterbatch Code")
    with c5:
        mb_ratio = st.number_input("MB Ratio (%)", step=0.1)

    st.divider()

    # Section 3: Process Parameters
    st.subheader("Process Settings")
    c6, c7, c8 = st.columns(3)
    with c6:
        inj_pressure = st.number_input("Injection Pressure (bar)")
        holding_pressure = st.number_input("Holding Pressure (bar)")
    with c7:
        melt_temp = st.number_input("Melt Temp (°C)")
        mold_temp = st.number_input("Mold Temp (°C)")
    with c8:
        cycle_time = st.number_input("Cycle Time (sec)", step=0.1)
        cooling_time = st.number_input("Cooling Time (sec)", step=0.1)

    st.divider()

    # Section 4: Observations
    notes = st.text_area("Trial Observations / Comments")

    # Submit Button
    submit_button = st.form_submit_button("Save Trial Data")

if submit_button:
    # Creating a dictionary for the new entry
    new_data = {
        "Date": [date],
        "Machine": [machine],
        "Operator": [operator],
        "Material": [material],
        "Cycle Time": [cycle_time],
        "Notes": [notes]
    }
    
    # Convert to DataFrame
    new_df = pd.DataFrame(new_data)
    
    # Logic to save to your .xlsm or .parquet file goes here
    st.success("Data successfully recorded!")
    st.balloons()
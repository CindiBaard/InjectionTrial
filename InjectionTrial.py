import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG & PATHS ---
st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")
# This is where you save your SUBMITTED trials
SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")

# --- DATA LOOKUP --- (Existing function remains the same)
def get_project_data(pre_prod_no):
    # ... (Your existing get_project_data code) ...
    pass

# --- NEW: TRIAL HISTORY FUNCTION ---
def display_trial_history(pre_prod_no):
    """Displays a timeline/table of previous trials for this ID."""
    if os.path.exists(SUBMISSIONS_FILE):
        df = pd.read_parquet(SUBMISSIONS_FILE)
        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date')
        
        if not history.empty:
            st.info(f"Total Trials for {pre_prod_no}: **{len(history)}**")
            # Show a simplified timeline/table
            st.dataframe(history[['Trial Ref', 'Date', 'Operator', 'Observations']], use_container_width=True)
        else:
            st.write("No previous trials recorded for this project.")

# --- INITIALIZE SESSION STATE ---
if 'lookup_data' not in st.session_state:
    st.session_state.lookup_data = {}

# --- HEADER & SEARCH ---
st.title("Injection Trial Data Entry")
search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

if st.button("Pull Information"):
    if search_input:
        data = get_project_data(search_input)
        if data:
            st.session_state.lookup_data = data
            st.rerun()

st.divider()

# --- TRIAL SUMMARY / TIMELINE ---
if search_input:
    st.subheader(f"Trial History for: {search_input}")
    display_trial_history(search_input)
    st.divider()

# --- MAIN FORM ---
if st.session_state.lookup_data:
    ld = st.session_state.lookup_data
    
    # Generate the auto-reference: e.g. 11925_T2
    trial_ref = get_next_trial_reference(search_input, SUBMISSIONS_FILE)

    with st.form("injection_xlsm_form", clear_on_submit=True):
        st.subheader(f"New Entry: {trial_ref}") # Visual confirmation of Trial No.
        
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            date = st.date_input("Date", datetime.now())
            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))
        with s2:
            # We store the unique reference here
            job_no = st.text_input("Pre-Prod No.", value=search_input, disabled=True)
            current_ref = st.text_input("Trial Reference", value=trial_ref, disabled=True)
        # ... [Rest of your columns s3, s4 and Sections 2-5 remain the same] ...

        submit_trial = st.form_submit_button("Submit Trial Entry")

    if submit_trial:
        # Create a dictionary of the form data
        new_data = {
            "Trial Ref": trial_ref,
            "Pre-Prod No.": search_input,
            "Date": date.strftime("%Y-%m-%d"),
            "Operator": operator,
            "Observations": notes,
            # ... Add all other form fields here ...
        }
        
        # LOGIC TO SAVE DATA
        df_new = pd.DataFrame([new_data])
        if os.path.exists(SUBMISSIONS_FILE):
            df_old = pd.read_parquet(SUBMISSIONS_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new
        
        df_final.to_parquet(SUBMISSIONS_FILE)
        
        st.success(f"Success! {trial_ref} recorded.")
        st.session_state.lookup_data = {}
        st.rerun()
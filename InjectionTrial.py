import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")

# ---- CONFIGURATION
# This is the sheet you use to check trial history
REF_FILE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y" 
# This is the Project Tracker you want to update
TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"

# --- DIRECTORY SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")
SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")

# --- HELPER FUNCTIONS ---

def get_project_data(pre_prod_no):
    if not os.path.exists(FILENAME_PARQUET):
        st.error(f"Database file not found at: {FILENAME_PARQUET}")
        return None
    try:
        df_tracker = pd.read_parquet(FILENAME_PARQUET)
        col_name = "Pre-Prod No." 
        search_term = str(pre_prod_no).strip()
        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        result = df_tracker[df_tracker[col_name] == search_term]
        return result.iloc[0].to_dict() if not result.empty else None
    except Exception as e:
        st.error(f"Error reading project database: {e}")
    return None

def get_next_trial_reference(pre_prod_no):
    if not os.path.exists(SUBMISSIONS_FILE):
        return f"{pre_prod_no}_T1"
    try:
        df_history = pd.read_parquet(SUBMISSIONS_FILE)
        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]
        count = len(existing_trials)
        return f"{pre_prod_no}_T{count + 1}"
    except:
        return f"{pre_prod_no}_T1"

def update_tracker_status(pre_prod_no, current_trial_ref):
    """
    Updates the Project Tracker Google Sheet with 'T# - DD/MM/YYYY'
    """
    import gspread
    from google.oauth2.service_account import Credentials
    
    try:
        # 1. Credentials Setup
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]
        if isinstance(creds_info, dict) and "private_key" in creds_info:
             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # 2. Open Project Tracker Spreadsheet
        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)
        tracker_worksheet = tracker_spreadsheet.get_worksheet(0) 
        
        # 3. Padding logic for ID matching
        def pad_id(val):
            val_str = str(val).strip().split('.')[0]
            if '_' in val_str:
                parts = val_str.split('_', 1)
                return f"{parts[0].zfill(5)}_{parts[1]}"
            return val_str.zfill(5)

        search_id = pad_id(pre_prod_no)

        # 4. Find the Row
        cell = tracker_worksheet.find(search_id, in_column=1)
        row_idx = cell.row

        # 5. Prepare the Combined Value (e.g., T1 - 10/04/2026)
        trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref
        current_date = datetime.now().strftime('%d/%m/%Y')
        combined_value = f"{trial_suffix} - {current_date}"

        # 6. Find Column "Injection trial requested"
        headers = [h.strip() for h in tracker_worksheet.row_values(1)]
        col_name = "Injection trial requested"
        
        if col_name in headers:
            col_idx = headers.index(col_name) + 1
            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)
            return True, combined_value
        else:
            return False, f"Column '{col_name}' not found in Google Sheet headers."

    except Exception as e:
        return False, str(e)

# --- UI LOGIC ---
st.title("Injection Trial Data Entry")
search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

if st.button("Pull Information"):
    if search_input:
        data = get_project_data(search_input)
        if data:
            st.session_state.lookup_data = data
            st.success(f"Project details loaded for {search_input}")
        else:
            st.warning("No project data found.")

if search_input:
    ld = st.session_state.get('lookup_data', {})
    current_trial_ref = get_next_trial_reference(search_input)

    with st.form("trial_form"):
        st.subheader(f"New Trial Entry: {current_trial_ref}")
        operator = st.text_input("Operator")
        notes = st.text_area("Observations")
        submit_trial = st.form_submit_button("Submit Trial Entry")

        if submit_trial:
            with st.status("Processing...") as status:
                # 1. Update Local Parquet (Logic remains the same)
                # ... [Your existing parquet saving code goes here] ...

                # 2. Update Google Sheet
                st.write("🌐 Syncing with Project Tracker...")
                # CRITICAL FIX: Passing both arguments here
                success, result_msg = update_tracker_status(search_input, current_trial_ref)
                
                if success:
                    st.success(f"✅ Tracker Updated: {result_msg}")
                    status.update(label="Sync Complete", state="complete")
                else:
                    st.error(f"❌ Sync Failed: {result_msg}")
                    status.update(label="Local Saved, Cloud Failed", state="error")
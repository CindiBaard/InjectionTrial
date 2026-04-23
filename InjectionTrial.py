import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")

# --- CONFIGURATION ---
# 1. The Master Project Tracker (where we pull info and update status)
MASTER_TRACKER_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"

# 2. The Trial Timeline (where we save the 39 columns of history)
TRIAL_TIMELINE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"

# --- DIRECTORY SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")
SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")

# --- HELPER FUNCTIONS ---

def get_project_data(pre_prod_no):
    """Searches the combined parquet file for the Pre-Prod number."""
    if not os.path.exists(FILENAME_PARQUET):
        st.error(f"Database file not found at: {FILENAME_PARQUET}")
        return None
    try:
        df_tracker = pd.read_parquet(FILENAME_PARQUET)
        col_name = "Pre-Prod No." 
        if col_name not in df_tracker.columns:
            st.error(f"Column '{col_name}' not found.")
            return None
        search_term = str(pre_prod_no).strip()
        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        result = df_tracker[df_tracker[col_name] == search_term]
        return result.iloc[0].to_dict() if not result.empty else None
    except Exception as e:
        st.error(f"Error reading project database: {e}")
    return None

def get_next_trial_reference(pre_prod_no):
    """Calculates the next trial number by checking submission history."""
    if not os.path.exists(SUBMISSIONS_FILE):
        return f"{pre_prod_no}_T1"
    try:
        df_history = pd.read_parquet(SUBMISSIONS_FILE)
        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]
        count = len(existing_trials)
        return f"{pre_prod_no}_T{count + 1}"
    except:
        return f"{pre_prod_no}_T1"

def delete_trial_entry(trial_ref):
    """Removes a trial from local parquet and returns the Pre-Prod No. to trigger a sync."""
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            df = pd.read_parquet(SUBMISSIONS_FILE)
            # Find the Pre-Prod No. before we delete the row
            target_row = df[df['Trial Reference'] == trial_ref]
            if target_row.empty:
                return False, None
            
            pre_prod_no = target_row.iloc[0]['Pre-Prod No.']
            
            # Perform deletion
            df_filtered = df[df['Trial Reference'] != trial_ref]
            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)
            
            return True, pre_prod_no
        except Exception as e:
            st.error(f"Error deleting entry: {e}")
            return False, None
    return False, None

# --- PAGE CONFIGURATION ---

st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")



# ---- CONFIGURATION

# The ID of your Project Tracker spreadsheet

TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"



# --- DIRECTORY SETUP ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")



# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            # Keep everything EXCEPT the trial reference we want to delete

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        # Filter for the specific project

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

           

            # Create a clean display table

            display_df = history[['Trial Ref', 'Date', 'Operator', 'Observations']].copy()

           

            # Using columns to create a "Delete" interface

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    # Unique key required for each button in a loop

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1) # Brief pause so user sees success

                            st.rerun() # Refresh to update the list

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    """Updates the Project Tracker Google Sheet with 'T# - Date'"""

    import gspread

    from google.oauth2.service_account import Credentials



    # 1. Construct the value for the Google Sheet (e.g., T1 - 17/04/2026)

    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        # If manual_date is coming from history (e.g. "2026-04-20"),

        # you might need to format it to DD/MM/YYYY

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Use your existing secrets logic

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        # Helper to match IDs

        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row



        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."



    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    """Finds the most recent trial in history and pushes it to Google Sheets."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, "No history file found."

   

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            # If no trials left, you might want to clear the cell or set to "No Trials"

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        # Extract number to sort correctly (T10 comes after T2)

        project_history['Trial_Num'] = project_history['Trial Ref'].str.extract(r'(\d+)$').astype(int)

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(

            pre_prod_no,

            latest_trial['Trial Ref'],

            manual_date=latest_trial['Date']

        )

    except Exception as e:

        return False, str(e)  

   

    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)

       

# FIX STARTS HERE

        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            val_str = str(input_val).strip().split('.')[0]

            if '_' in val_str:

                parts = val_str.split('_', 1)

                return f"{parts[0]}_{parts[1]}"

            return val_str



        # Pass the pre_prod_no into the helper function

        search_id = pad_id(pre_prod_no)

       

        st.write(f"Searching for ID: {search_id}") # Helpful for debugging

        cell = tracker_worksheet.find(search_id, in_column=1)



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row



        # Construct: T1 - 10/04/2026

        trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

        current_date = datetime.now().strftime('%d/%m/%Y')

        combined_value = f"{trial_suffix} - {current_date}"



        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



from fpdf import FPDF

import io



# --- PDF GENERATION HELPER ---

def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

   

    # Title

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

   

    # Table-like content

    pdf.set_font("Arial", size=12)

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{value}", border=0, ln=True)

   

    # Return as bytes

    return pdf.output(dest='S').encode('latin-1')



# ... [Keep all your existing code until the form submission] ...



# --- NEW TRIAL ENTRY FORM ---

    # Ensure this block is indented once under 'if search_input:'

    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        # ... (Your existing columns s1-s4, p1-p4, d1-d5, pr1-pr4, and notes) ...

        # [Keep all your input fields here]

       

        # This button MUST be indented exactly the same as the st.subheader lines above

        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            # 1. Capture data for PDF

            st.session_state.last_submission_data = {

                "Trial Reference": current_trial_ref,

                "Pre-Prod No.": search_input,

                "Date": trial_date.strftime("%Y-%m-%d"),

                "Client": client,

                "Operator": operator,

                "Cycle Time": f"{cyc_t}s",

                "Inj Pressure": f"{inj_p} bar",

                "Observations": notes

            }



            with st.status("Saving Data...", expanded=True) as status:

                # ... [YOUR EXISTING DATABASE/GSHEETS SAVE CODE] ...

               

                status.update(label="Submission Processed!", state="complete", expanded=False)

                st.session_state.submitted = True



    # --- PDF & RESET SECTION (OUTSIDE THE FORM) ---

    # This 'if' must be aligned with the 'with st.form' line above

    if st.session_state.get('submitted', False):

        st.success("Entry Saved Successfully!")

       

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.lookup_data = {}

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()



# --- PDF GENERATION HELPER ---

def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

    pdf.set_font("Arial", size=12)

   

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{str(value)}", border=0, ln=True)

   

    return pdf.output(dest='S').encode('latin-1')

               

# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- TRIAL TIMELINE & SYNC SECTION ---

if search_input:

    st.subheader(f"Trial Timeline: {search_input}")

   

    # Add a Sync button at the top of the history section

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            # This calls the helper function you added earlier

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated to last valid trial!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    # Display the actual history (with the delete buttons)

    display_trial_history(search_input)

    st.divider()



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared! Try searching again.")



# --- NEW TRIAL ENTRY FORM ---

if search_input:

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()



        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("If no dosing unit, what % pre-mixed?",

                                      value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

       

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()



        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()



        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                st.write("📝 Writing to trial history...")

               

                new_submission = {

                    "Trial Ref": current_trial_ref,

                    "Pre-Prod No.": str(search_input),

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": sales_rep,

                    "Client": client,

                    "Operator": operator,

                    "Observations": notes,

                    "Cycle Time": cyc_t,

                    "Inj Pressure": inj_p,

                    "Tinuvin": tinuvin_val,

                    "Dosing Unit Fitted": dosing_fitted,

                    "Dosing Calibrated": dosing_calib,

                    "Colour Set": colour_set,

                    "Shot Weight": shot_w

                }



                # Save to Trial_Submissions.parquet

                df_new = pd.DataFrame([new_submission])

                if os.path.exists(SUBMISSIONS_FILE):

                    df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                    df_final = pd.concat([df_existing, df_new], ignore_index=True)

                else:

                    df_final = df_new

                df_final.to_parquet(SUBMISSIONS_FILE, index=False)

                st.write("✅ Trial history log updated.")



                # --- UPDATE LOCAL TRACKER FILE ---

                st.write("💾 Updating local Project Tracker file...")

                if os.path.exists(FILENAME_PARQUET):

                    df_tracker = pd.read_parquet(FILENAME_PARQUET)

                   

                    def pad_id_local(val):

                        return str(val).strip().split('.')[0].zfill(5)

                   

                    search_id = pad_id_local(search_input)

                    df_tracker['Pre-Prod No.'] = df_tracker['Pre-Prod No.'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().apply(lambda x: x.zfill(5))

                   

                    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

                    combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"

                   

                    mask = df_tracker['Pre-Prod No.'] == search_id

                    if mask.any():

                        df_tracker.loc[mask, 'Injection trial requested'] = combined_value

                        df_tracker.to_parquet(FILENAME_PARQUET, index=False)

                        st.write("✅ Local Project Tracker updated.")

                    else:

                        st.warning("Could not find ID in local Parquet to update.")



                # --- GOOGLE SHEETS UPDATE ---

                st.write("🌐 Attempting Cloud Sync (Google Sheets)...")

                success, msg = update_tracker_status(search_input, current_trial_ref)

               

                if success:

                    st.write(f"✅ Cloud Sync Complete: {msg}")

                    status.update(label="Submission Processed & Synced!", state="complete", expanded=False)

                    st.session_state.submitted = True

                    st.cache_data.clear()

                else:

                    st.error(f"❌ Cloud Sync Failed: {msg}")

                    status.update(label="Local Saved, Cloud Sync Failed", state="error", expanded=True)



    # UI Feedback and Reset

    if st.session_state.get('submitted', False):

        st.success("Entry Saved Successfully!")

        if st.button("Start Next Entry"):

            st.session_state.lookup_data = {}

            st.session_state.submitted = False

            st.rerun(): The previously saved trials are not pulling through to the InjectionTrial file:

def sync_last_trial_to_cloud(pre_prod_no):
    """Finds the most recent trial in history and pushes it to Google Sheets."""
    # Ensure we use the absolute path defined at the top
    if not os.path.exists(SUBMISSIONS_FILE):
        return False, f"No history file found at {SUBMISSIONS_FILE}. Please submit a trial first."
    
    try:
        df_history = pd.read_parquet(SUBMISSIONS_FILE)
        # Convert column to string to ensure matching works
        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)
        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()
        
        if project_history.empty:
            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials") 

        # Extract number to sort correctly (handles T1, T2, T10 etc)
        project_history['Trial_Num'] = project_history['Trial Ref'].str.extract(r'(\d+)$').astype(int)
        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]
        
        return update_tracker_status(
            pre_prod_no, 
            latest_trial['Trial Ref'], 
            manual_date=latest_trial['Date']
        )
    except Exception as e:
        return False, str(e)
Part B: Corrected UI Logic (PDF & Reset)
Move the PDF download block above the form or ensure it is handled correctly within the if search_input logic. The version below ensures that once st.session_state.submitted is True, the button appears.

Python
# --- NEW TRIAL ENTRY FORM ---
if search_input:
    ld = st.session_state.get('lookup_data', {})
    current_trial_ref = get_next_trial_reference(search_input)

    # --- SUCCESS & PDF SECTION ---
    # We check this BEFORE the form so it appears at the top once submitted
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        
        if 'last_submission_data' in st.session_state:
            try:
                pdf_bytes = create_pdf(st.session_state.last_submission_data)
                st.download_button(
                    label="📥 Download Trial Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",
                    mime="application/pdf",
                    key="download_pdf_main"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
        
        if st.button("Start Next Entry"):
            st.session_state.submitted = False 
            if 'last_submission_data' in st.session_state:
                del st.session_state.last_submission_data
            st.rerun()
        
        st.divider() # Separate success message from the form below

    # Only show the form if not just submitted, or keep it there for back-to-back entries
    with st.form("injection_xlsm_form", clear_on_submit=True):
        # ... [Your existing form fields: s1, p1, d1, pr1, etc.] ...
        
        submit_trial = st.form_submit_button("Submit Trial Entry")

        if submit_trial:
            # Create the data dictionary for the PDF
            st.session_state.last_submission_data = {
                "Trial Reference": current_trial_ref,
                "Pre-Prod No.": search_input,
                "Date": trial_date.strftime("%Y-%m-%d"),
                "Client": client,
                "Operator": operator,
                "Cycle Time": f"{cyc_t}s",
                "Inj Pressure": f"{inj_p} bar",
                "Observations": notes
            }
            
            # ... [Your saving logic to Parquet and Google Sheets] ...
            
            st.session_state.submitted = True
            st.rerun() # Rerun to show the success message and PDF button
Why the Sync was failing:
Pathing: If you are running Streamlit locally vs. on a server, os.path.abspath(__file__) might point to different spots. Check that Trial_Submissions.parquet actually exists in the same folder as your script.

Data Types: Parquet files often save "11925" as an integer, but your search might be looking for a string "11925". Adding .astype(str) during the sync helps bridge that gap.

To see the PDF Button:
I moved the logic so that as soon as submit_trial finishes, it triggers st.rerun(). On the next pass, the app sees st.session_state.submitted == True and immediately displays the Download PDF button at the top of the page.

NameError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/injectiontrial/InjectionTrial.py", line 254, in <module>

if search_input:

^^^^^^^^^^^^

The NameError on search_input typically means you are trying to use that variable in your code before it has actually been defined, or it was defined inside a conditional block (like an if statement) that didn't run.

In your script, this usually happens because of the order of operations. Streamlit runs your script from top to bottom every time something changes.

The Fix
You need to move your Header & Search section (where search_input is defined) to the top of your script, or at least before the Trial Timeline and New Trial Entry sections.

Here is the corrected flow for your script:

Python
# 1. Imports and Config (Already at top)
import streamlit as st
# ... 

# 2. Helper Functions (Already at top)
# ...

# 3. Initialize Session State (Add this near the top)
if 'lookup_data' not in st.session_state:
    st.session_state.lookup_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# 4. Define search_input FIRST
st.title("Injection Trial Data Entry")
st.subheader("Search Project Tracker")

col_s1, col_s2 = st.columns([1, 3])
with col_s1:
    # Defining the variable here ensures it exists for the rest of the script
    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):") 

with col_s2:
    st.write("##") 
    if st.button("Pull Information"):
        if search_input:
            data = get_project_data(search_input)
            if data:
                st.session_state.lookup_data = data
                st.success(f"Project details loaded.")
            else:
                st.warning("No project data found.")
                st.session_state.lookup_data = {}

# 5. Now you can safely use "if search_input:"
if search_input:
    # All your Trial Timeline, Sync, and Form logic goes here
    # ...
Why this happened
In your original code, you had the Trial Timeline logic using if search_input: positioned above the actual line where search_input = st.text_input(...) was written.

When the app starts, it tries to read the if search_input: line, but since Python hasn't reached the text_input line yet, it has no idea what search_input is—hence the NameError.

Regarding the "No history file found"
Double-check your SUBMISSIONS_FILE variable:

Ensure SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet") is correct.

If you are on Streamlit Cloud, remember that files saved to the local directory are temporary. If the app reboots or "sleeps," the .parquet file might be deleted.

Recommendation: For persistent storage on the cloud, it is usually safer to save the trial data to a separate Google Sheet or a database (like Supabase or Snowflake) rather than a local Parquet file.

Regarding the PDF Button
Once you move the search input to the top and resolve the NameError, ensure the PDF download code is not inside the with st.form block. It should stay outside so that the "Submit" action can trigger a rerun and display the button.

where must this code be inserted. Must it go directly after the code I've copied and pasted? # 3. Initialize Session State (Add this near the top)if 'lookup_data' not in st.session_state:

st.session_state.lookup_data = {}if 'submitted' not in st.session_state:

st.session_state.submitted = False# 4. Define search_input FIRST

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])with col_s1:

# Defining the variable here ensures it exists for the rest of the script

search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):") with col_s2:

st.write("##")

if st.button("Pull Information"):

if search_input:

data = get_project_data(search_input)

if data:

st.session_state.lookup_data = data

st.success(f"Project details loaded.")

else:

st.warning("No project data found.")

st.session_state.lookup_data = {}# 5. Now you can safely use "if search_input:"if search_input:

# All your Trial Timeline, Sync, and Form logic goes here

# ...# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            # Keep everything EXCEPT the trial reference we want to delete

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        # Filter for the specific project

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

           

            # Create a clean display table

            display_df = history[['Trial Ref', 'Date', 'Operator', 'Observations']].copy()

           

            # Using columns to create a "Delete" interface

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    # Unique key required for each button in a loop

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1) # Brief pause so user sees success

                            st.rerun() # Refresh to update the list

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    """Updates the Project Tracker Google Sheet with 'T# - Date'"""

    import gspread

    from google.oauth2.service_account import Credentials



    # 1. Construct the value for the Google Sheet (e.g., T1 - 17/04/2026)

    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        # If manual_date is coming from history (e.g. "2026-04-20"),

        # you might need to format it to DD/MM/YYYY

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Use your existing secrets logic

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        # Helper to match IDs

        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row



        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."



    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    """Finds the most recent trial in history and pushes it to Google Sheets."""

    # Ensure we use the absolute path defined at the top

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, f"No history file found at {SUBMISSIONS_FILE}. Please submit a trial first."

   

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        # Convert column to string to ensure matching works

        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        # Extract number to sort correctly (handles T1, T2, T10 etc)

        project_history['Trial_Num'] = project_history['Trial Ref'].str.extract(r'(\d+)$').astype(int)

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(

            pre_prod_no,

            latest_trial['Trial Ref'],

            manual_date=latest_trial['Date']

        )

    except Exception as e:

        return False, str(e)

   

    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)

       

# FIX STARTS HERE

        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            val_str = str(input_val).strip().split('.')[0]

            if '_' in val_str:

                parts = val_str.split('_', 1)

                return f"{parts[0]}_{parts[1]}"

            return val_str



        # Pass the pre_prod_no into the helper function

        search_id = pad_id(pre_prod_no)

       

        st.write(f"Searching for ID: {search_id}") # Helpful for debugging

        cell = tracker_worksheet.find(search_id, in_column=1)



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row



        # Construct: T1 - 10/04/2026

        trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

        current_date = datetime.now().strftime('%d/%m/%Y')

        combined_value = f"{trial_suffix} - {current_date}"



        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



from fpdf import FPDF

import io



# --- PDF GENERATION HELPER ---

def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

   

    # Title

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

   

    # Table-like content

    pdf.set_font("Arial", size=12)

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{value}", border=0, ln=True)

   

    # Return as bytes

    return pdf.output(dest='S').encode('latin-1')



# ... [Keep all your existing code until the form submission] ...

No, you should not just paste it at the end. Because Python reads your script from top to bottom, the NameError happens because the code is trying to use search_input before it has been created.

To fix this, you need to reorganize your script into a specific order. Follow this structure:

1. The Very Top: Imports and Config
Keep your import statements and the st.set_page_config at the very top.

2. The Middle: Helper Functions
Keep all your def functions (like get_project_data, create_pdf, etc.) here.

3. The Bottom: The "App Logic" (Order is Critical)
This is where the fix happens. You must define your session state and the search input before the code that uses them.

Here is exactly how that bottom section should look:

Python
# --- INITIALIZE SESSION STATE ---
# This must happen before any logic runs
if 'lookup_data' not in st.session_state:
    st.session_state.lookup_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- HEADER & SEARCH ---
st.title("Injection Trial Data Entry")
st.subheader("Search Project Tracker")

col_s1, col_s2 = st.columns([1, 3])
with col_s1:
    # We define search_input HERE. Now everything below knows what it is.
    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):") 

with col_s2:
    st.write("##") 
    if st.button("Pull Information"):
        if search_input:
            data = get_project_data(search_input)
            if data:
                st.session_state.lookup_data = data
                st.success("Project details loaded.")
            else:
                st.warning("No project data found.")
                st.session_state.lookup_data = {}

st.divider()

# --- THE MAIN LOGIC (Safe to use search_input now) ---
if search_input:
    # 1. Trial Timeline & Sync Section
    st.subheader(f"Trial Timeline: {search_input}")
    
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")
    with col_h2:
        if st.button("🔄 Sync Master Tracker"):
            success, msg = sync_last_trial_to_cloud(search_input)
            if success:
                st.success("Master Tracker updated!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Sync failed: {msg}")

    display_trial_history(search_input)
    st.divider()

    # 2. PDF Download Section (Shows after submission)
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        if 'last_submission_data' in st.session_state:
            pdf_bytes = create_pdf(st.session_state.last_submission_data)
            st.download_button(
                label="📥 Download Trial Report (PDF)",
                data=pdf_bytes,
                file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",
                mime="application/pdf"
            )
        if st.button("Start Next Entry"):
            st.session_state.submitted = False
            st.rerun()

    # 3. New Trial Entry Form
    # [Insert your existing st.form code here...]
Why this fixes the error:
Sequence: By putting search_input = st.text_input(...) near the top of your "App Logic," the variable is created immediately.

Scope: Any code that sits inside the if search_input: block will only run when there is text in that box, preventing errors on page load.

Visibility: Placing the PDF Download logic above the form (but still inside the if search_input block) ensures it is the first thing the operator sees after the page refreshes from a successful save.

NameError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/injectiontrial/InjectionTrial.py", line 254, in <module>

if search_input: # --- NEW TRIAL ENTRY FORM ---

if search_input:

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    # --- SUCCESS & PDF SECTION ---

    # We check this BEFORE the form so it appears at the top once submitted

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

       

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf_main"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()

       

        st.divider() # Separate success message from the form below



    # Only show the form if not just submitted, or keep it there for back-to-back entries

    with st.form("injection_xlsm_form", clear_on_submit=True):

        # ... [Your existing form fields: s1, p1, d1, pr1, etc.] ...

       

        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            # Create the data dictionary for the PDF

            st.session_state.last_submission_data = {

                "Trial Reference": current_trial_ref,

                "Pre-Prod No.": search_input,

                "Date": trial_date.strftime("%Y-%m-%d"),

                "Client": client,

                "Operator": operator,

                "Cycle Time": f"{cyc_t}s",

                "Inj Pressure": f"{inj_p} bar",

                "Observations": notes

            }

           

            # ... [Your saving logic to Parquet and Google Sheets] ...

           

            st.session_state.submitted = True

            st.rerun() # Rerun to show the success message and PDF button



# --- PDF GENERATION HELPER ---

def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

    pdf.set_font("Arial", size=12)

   

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{str(value)}", border=0, ln=True)

   

    return pdf.output(dest='S').encode('latin-1')



# This must happen before any logic runs

if 'lookup_data' not in st.session_state:

    st.session_state.lookup_data = {}

if 'submitted' not in st.session_state:

    st.session_state.submitted = False

               

# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- TRIAL TIMELINE & SYNC SECTION ---

if search_input:

    st.subheader(f"Trial Timeline: {search_input}")

   

    # Add a Sync button at the top of the history section

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            # This calls the helper function you added earlier

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated to last valid trial!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    # Display the actual history (with the delete buttons)

    display_trial_history(search_input)

    st.divider()



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared! Try searching again.")



# 2. PDF Download Section (Shows after submission)

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

        if 'last_submission_data' in st.session_state:

            pdf_bytes = create_pdf(st.session_state.last_submission_data)

            st.download_button(

                label="📥 Download Trial Report (PDF)",

                data=pdf_bytes,

                file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                mime="application/pdf"

            )

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            st.rerun()



# --- NEW TRIAL ENTRY FORM ---

if search_input:

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()



        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("If no dosing unit, what % pre-mixed?",

                                      value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

       

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()



        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()



        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                st.write("📝 Writing to trial history...")

               

                new_submission = {

                    "Trial Ref": current_trial_ref,

                    "Pre-Prod No.": str(search_input),

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": sales_rep,

                    "Client": client,

                    "Operator": operator,

                    "Observations": notes,

                    "Cycle Time": cyc_t,

                    "Inj Pressure": inj_p,

                    "Tinuvin": tinuvin_val,

                    "Dosing Unit Fitted": dosing_fitted,

                    "Dosing Calibrated": dosing_calib,

                    "Colour Set": colour_set,

                    "Shot Weight": shot_w

                }



                # Save to Trial_Submissions.parquet

                df_new = pd.DataFrame([new_submission])

                if os.path.exists(SUBMISSIONS_FILE):

                    df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                    df_final = pd.concat([df_existing, df_new], ignore_index=True)

                else:

                    df_final = df_new

                df_final.to_parquet(SUBMISSIONS_FILE, index=False)

                st.write("✅ Trial history log updated.")



                # --- UPDATE LOCAL TRACKER FILE ---

                st.write("💾 Updating local Project Tracker file...")

                if os.path.exists(FILENAME_PARQUET):

                    df_tracker = pd.read_parquet(FILENAME_PARQUET)

                   

                    def pad_id_local(val):

                        return str(val).strip().split('.')[0].zfill(5)

                   

                    search_id = pad_id_local(search_input)

                    df_tracker['Pre-Prod No.'] = df_tracker['Pre-Prod No.'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().apply(lambda x: x.zfill(5))

                   

                    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

                    combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"

                   

                    mask = df_tracker['Pre-Prod No.'] == search_id

                    if mask.any():

                        df_tracker.loc[mask, 'Injection trial requested'] = combined_value

                        df_tracker.to_parquet(FILENAME_PARQUET, index=False)

                        st.write("✅ Local Project Tracker updated.")

                    else:

                        st.warning("Could not find ID in local Parquet to update.")



                # --- GOOGLE SHEETS UPDATE ---

                st.write("🌐 Attempting Cloud Sync (Google Sheets)...")

                success, msg = update_tracker_status(search_input, current_trial_ref)

               

                if success:

                    st.write(f"✅ Cloud Sync Complete: {msg}")

                    status.update(label="Submission Processed & Synced!", state="complete", expanded=False)

                    st.session_state.submitted = True

                    st.cache_data.clear()

                else:

                    st.error(f"❌ Cloud Sync Failed: {msg}")

                    status.update(label="Local Saved, Cloud Sync Failed", state="error", expanded=True)



    # UI Feedback and Reset

    if st.session_state.get('submitted', False):

        st.success("Entry Saved Successfully!")

        if st.button("Start Next Entry"):

            st.session_state.lookup_data = {}

            st.session_state.submitted = False

            st.rerun()

^^^^^^^^^^^^

The NameError is occurring because your script is trying to use the variable search_input (at line 254) before the code that actually creates it (the st.text_input part) has been executed.

In Streamlit, the order of code is the order of execution. You have your "Logic" blocks at the very top of the file, but your "UI" blocks (where the user actually types the ID) at the bottom.

The Solution: Reorder Your Script
You need to move your Session State and Header & Search blocks to the top of your script's execution flow (right after your imports and helper functions).

Step 1: Place this right after your Helper Functions
Move these blocks to the top. This ensures search_input is defined globally for the rest of the script to see.

Python
# --- INITIALIZE SESSION STATE ---
if 'lookup_data' not in st.session_state:
    st.session_state.lookup_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- HEADER & SEARCH ---
st.title("Injection Trial Data Entry")
st.subheader("Search Project Tracker")

col_s1, col_s2 = st.columns([1, 3])
with col_s1:
    # DEFINING THE VARIABLE HERE
    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")
with col_s2:
    st.write("##") 
    if st.button("Pull Information"):
        if search_input:
            data = get_project_data(search_input)
            if data:
                st.session_state.lookup_data = data
                st.success(f"Project details loaded for {search_input}")
            else:
                st.warning("No project data found.")
                st.session_state.lookup_data = {}

st.divider()
Step 2: Wrap your Logic in "if search_input:"
Now that search_input exists, move your Trial Timeline and Form logic below the search block, inside an if search_input: check. This prevents the app from trying to run calculations on a blank input.

Python
if search_input:
    # 1. TRIAL TIMELINE & SYNC SECTION
    st.subheader(f"Trial Timeline: {search_input}")
    # ... [Insert your Sync button and display_trial_history code here] ...

    # 2. SUCCESS & PDF SECTION
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        # ... [Insert your PDF download button logic here] ...

    # 3. NEW TRIAL ENTRY FORM
    ld = st.session_state.get('lookup_data', {})
    current_trial_ref = get_next_trial_reference(search_input)
    
    with st.form("injection_xlsm_form", clear_on_submit=True):
        # ... [Insert all your form fields and submission logic here] ...
Summary of the Correct Flow
Imports: (Pandas, Streamlit, FPDF, etc.)

Helper Functions: (create_pdf, get_project_data, etc.)

Session State Initialization: (st.session_state.submitted, etc.)

Search Input: (search_input = st.text_input...)

Conditional Content: (if search_input:) — All forms and history go inside here.

A Quick Tip on the PDF Button
Because you are using st.rerun() after a successful submission, the st.download_button must be placed before the st.form block (but still inside the if search_input: block). This ensures that when the page refreshes, the user sees the download button at the top of the page immediately.

PLEASE CORRECT THE CODE FOR ME. i.e. move the code blocks to the correct position but don't change anything else: import streamlit as st

import pandas as pd

from datetime import datetime

import os

import time



# --- PAGE CONFIGURATION ---

st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")



# ---- CONFIGURATION

# The ID of your Project Tracker spreadsheet

TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"



# --- DIRECTORY SETUP ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")



# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            # Keep everything EXCEPT the trial reference we want to delete

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        # Filter for the specific project

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

           

            # Create a clean display table

            display_df = history[['Trial Ref', 'Date', 'Operator', 'Observations']].copy()

           

            # Using columns to create a "Delete" interface

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    # Unique key required for each button in a loop

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1) # Brief pause so user sees success

                            st.rerun() # Refresh to update the list

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    """Updates the Project Tracker Google Sheet with 'T# - Date'"""

    import gspread

    from google.oauth2.service_account import Credentials



    # 1. Construct the value for the Google Sheet (e.g., T1 - 17/04/2026)

    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        # If manual_date is coming from history (e.g. "2026-04-20"),

        # you might need to format it to DD/MM/YYYY

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Use your existing secrets logic

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        # Helper to match IDs

        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row



        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."



    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    """Finds the most recent trial in history and pushes it to Google Sheets."""

    # Ensure we use the absolute path defined at the top

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, f"No history file found at {SUBMISSIONS_FILE}. Please submit a trial first."

   

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        # Convert column to string to ensure matching works

        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        # Extract number to sort correctly (handles T1, T2, T10 etc)

        project_history['Trial_Num'] = project_history['Trial Ref'].str.extract(r'(\d+)$').astype(int)

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(

            pre_prod_no,

            latest_trial['Trial Ref'],

            manual_date=latest_trial['Date']

        )

    except Exception as e:

        return False, str(e)

   

    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)

       

# FIX STARTS HERE

        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            val_str = str(input_val).strip().split('.')[0]

            if '_' in val_str:

                parts = val_str.split('_', 1)

                return f"{parts[0]}_{parts[1]}"

            return val_str



        # Pass the pre_prod_no into the helper function

        search_id = pad_id(pre_prod_no)

       

        st.write(f"Searching for ID: {search_id}") # Helpful for debugging

        cell = tracker_worksheet.find(search_id, in_column=1)



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row



        # Construct: T1 - 10/04/2026

        trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

        current_date = datetime.now().strftime('%d/%m/%Y')

        combined_value = f"{trial_suffix} - {current_date}"



        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



from fpdf import FPDF

import io



# --- PDF GENERATION HELPER ---

def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

   

    # Title

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

   

    # Table-like content

    pdf.set_font("Arial", size=12)

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{value}", border=0, ln=True)

   

    # Return as bytes

    return pdf.output(dest='S').encode('latin-1')



# ... [Keep all your existing code until the form submission] ...



# --- NEW TRIAL ENTRY FORM ---

if search_input:

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    # --- SUCCESS & PDF SECTION ---

    # We check this BEFORE the form so it appears at the top once submitted

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

       

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf_main"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()

       

        st.divider() # Separate success message from the form below



    # Only show the form if not just submitted, or keep it there for back-to-back entries

    with st.form("injection_xlsm_form", clear_on_submit=True):

        # ... [Your existing form fields: s1, p1, d1, pr1, etc.] ...

       

        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            # Create the data dictionary for the PDF

            st.session_state.last_submission_data = {

                "Trial Reference": current_trial_ref,

                "Pre-Prod No.": search_input,

                "Date": trial_date.strftime("%Y-%m-%d"),

                "Client": client,

                "Operator": operator,

                "Cycle Time": f"{cyc_t}s",

                "Inj Pressure": f"{inj_p} bar",

                "Observations": notes

            }

           

            # ... [Your saving logic to Parquet and Google Sheets] ...

           

            st.session_state.submitted = True

            st.rerun() # Rerun to show the success message and PDF button



# --- PDF GENERATION HELPER ---

def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

    pdf.set_font("Arial", size=12)

   

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{str(value)}", border=0, ln=True)

   

    return pdf.output(dest='S').encode('latin-1')



# This must happen before any logic runs

if 'lookup_data' not in st.session_state:

    st.session_state.lookup_data = {}

if 'submitted' not in st.session_state:

    st.session_state.submitted = False

               

# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- TRIAL TIMELINE & SYNC SECTION ---

if search_input:

    st.subheader(f"Trial Timeline: {search_input}")

   

    # Add a Sync button at the top of the history section

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            # This calls the helper function you added earlier

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated to last valid trial!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    # Display the actual history (with the delete buttons)

    display_trial_history(search_input)

    st.divider()



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared! Try searching again.")



# 2. PDF Download Section (Shows after submission)

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

        if 'last_submission_data' in st.session_state:

            pdf_bytes = create_pdf(st.session_state.last_submission_data)

            st.download_button(

                label="📥 Download Trial Report (PDF)",

                data=pdf_bytes,

                file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                mime="application/pdf"

            )

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            st.rerun()



# --- NEW TRIAL ENTRY FORM ---

if search_input:

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()



        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("If no dosing unit, what % pre-mixed?",

                                      value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

       

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()



        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()



        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                st.write("📝 Writing to trial history...")

               

                new_submission = {

                    "Trial Ref": current_trial_ref,

                    "Pre-Prod No.": str(search_input),

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": sales_rep,

                    "Client": client,

                    "Operator": operator,

                    "Observations": notes,

                    "Cycle Time": cyc_t,

                    "Inj Pressure": inj_p,

                    "Tinuvin": tinuvin_val,

                    "Dosing Unit Fitted": dosing_fitted,

                    "Dosing Calibrated": dosing_calib,

                    "Colour Set": colour_set,

                    "Shot Weight": shot_w

                }



                # Save to Trial_Submissions.parquet

                df_new = pd.DataFrame([new_submission])

                if os.path.exists(SUBMISSIONS_FILE):

                    df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                    df_final = pd.concat([df_existing, df_new], ignore_index=True)

                else:

                    df_final = df_new

                df_final.to_parquet(SUBMISSIONS_FILE, index=False)

                st.write("✅ Trial history log updated.")



                # --- UPDATE LOCAL TRACKER FILE ---

                st.write("💾 Updating local Project Tracker file...")

                if os.path.exists(FILENAME_PARQUET):

                    df_tracker = pd.read_parquet(FILENAME_PARQUET)

                   

                    def pad_id_local(val):

                        return str(val).strip().split('.')[0].zfill(5)

                   

                    search_id = pad_id_local(search_input)

                    df_tracker['Pre-Prod No.'] = df_tracker['Pre-Prod No.'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().apply(lambda x: x.zfill(5))

                   

                    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

                    combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"

                   

                    mask = df_tracker['Pre-Prod No.'] == search_id

                    if mask.any():

                        df_tracker.loc[mask, 'Injection trial requested'] = combined_value

                        df_tracker.to_parquet(FILENAME_PARQUET, index=False)

                        st.write("✅ Local Project Tracker updated.")

                    else:

                        st.warning("Could not find ID in local Parquet to update.")



                # --- GOOGLE SHEETS UPDATE ---

                st.write("🌐 Attempting Cloud Sync (Google Sheets)...")

                success, msg = update_tracker_status(search_input, current_trial_ref)

               

                if success:

                    st.write(f"✅ Cloud Sync Complete: {msg}")

                    status.update(label="Submission Processed & Synced!", state="complete", expanded=False)

                    st.session_state.submitted = True

                    st.cache_data.clear()

                else:

                    st.error(f"❌ Cloud Sync Failed: {msg}")

                    status.update(label="Local Saved, Cloud Sync Failed", state="error", expanded=True)



    # UI Feedback and Reset

    if st.session_state.get('submitted', False):

        st.success("Entry Saved Successfully!")

        if st.button("Start Next Entry"):

            st.session_state.lookup_data = {}

            st.session_state.submitted = False

            st.rerun()

Here is the corrected code. I have reorganized it into a logical Streamlit execution flow: Imports > Helpers > Session State > Header/Search Input > Conditional UI (if search_input).

I also consolidated the duplicate create_pdf functions and logic blocks that were scattered at the bottom of your snippet.

Python
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")

# ---- CONFIGURATION
TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"

# --- DIRECTORY SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")
SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")

# --- HELPER FUNCTIONS ---

def get_project_data(pre_prod_no):
    """Searches the combined parquet file for the Pre-Prod number."""
    if not os.path.exists(FILENAME_PARQUET):
        st.error(f"Database file not found at: {FILENAME_PARQUET}")
        return None
    try:
        df_tracker = pd.read_parquet(FILENAME_PARQUET)
        col_name = "Pre-Prod No." 
        if col_name not in df_tracker.columns:
            st.error(f"Column '{col_name}' not found.")
            return None
        search_term = str(pre_prod_no).strip()
        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        result = df_tracker[df_tracker[col_name] == search_term]
        return result.iloc[0].to_dict() if not result.empty else None
    except Exception as e:
        st.error(f"Error reading project database: {e}")
    return None

def get_next_trial_reference(pre_prod_no):
    """Calculates the next trial number by checking submission history."""
    if not os.path.exists(SUBMISSIONS_FILE):
        return f"{pre_prod_no}_T1"
    try:
        df_history = pd.read_parquet(SUBMISSIONS_FILE)
        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]
        count = len(existing_trials)
        return f"{pre_prod_no}_T{count + 1}"
    except:
        return f"{pre_prod_no}_T1"

def delete_trial_entry(trial_ref):
    """Removes a specific trial reference from the submissions file."""
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            df = pd.read_parquet(SUBMISSIONS_FILE)
            df_filtered = df[df['Trial Ref'] != trial_ref]
            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Error deleting entry: {e}")
            return False
    return False

def display_trial_history(pre_prod_no):
    if os.path.exists(SUBMISSIONS_FILE):
        df = pd.read_parquet(SUBMISSIONS_FILE)
        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)
        
        if not history.empty:
            st.info(f"Existing Trials Found: **{len(history)}**")
            for index, row in history.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")
                    st.caption(f"Note: {row['Observations']}")
                with col2:
                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}"):
                        if delete_trial_entry(row['Trial Ref']):
                            st.success(f"Deleted {row['Trial Ref']}")
                            time.sleep(1) 
                            st.rerun()
                st.divider()
        else:
            st.write("No previous trial history found.")

def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):
    import gspread
    from google.oauth2.service_account import Credentials

    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref

    if manual_date:
        try:
            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")
            date_str = date_obj.strftime('%d/%m/%Y')
        except:
            date_str = manual_date
        combined_value = f"{trial_suffix} - {date_str}"
    else:
        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"

    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]
        if isinstance(creds_info, dict) and "private_key" in creds_info:
             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)
        tracker_worksheet = tracker_spreadsheet.get_worksheet(0) 

        def pad_id(input_val):
            if pd.isna(input_val) or str(input_val).strip() == '': 
                return ""
            return str(input_val).strip().split('.')[0]

        search_id = pad_id(pre_prod_no)
        cell = tracker_worksheet.find(search_id, in_column=1)
        row_idx = cell.row
        headers = [h.strip() for h in tracker_worksheet.row_values(1)]
        col_name = "Injection trial requested"
        
        if col_name in headers:
            col_idx = headers.index(col_name) + 1
            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)
            return True, combined_value
        else:
            return False, f"Column '{col_name}' not found."
    except Exception as e:
        return False, str(e)

def sync_last_trial_to_cloud(pre_prod_no):
    if not os.path.exists(SUBMISSIONS_FILE):
        return False, "No history file found."
    try:
        df_history = pd.read_parquet(SUBMISSIONS_FILE)
        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)
        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()
        
        if project_history.empty:
            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials") 

        project_history['Trial_Num'] = project_history['Trial Ref'].str.extract(r'(\d+)$').astype(int)
        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]
        
        return update_tracker_status(pre_prod_no, latest_trial['Trial Ref'], manual_date=latest_trial['Date'])
    except Exception as e:
        return False, str(e)

def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for key, value in data.items():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(50, 10, txt=f"{key}:", border=0)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 10, txt=f"{str(value)}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- INITIALIZE SESSION STATE ---
if 'lookup_data' not in st.session_state:
    st.session_state.lookup_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- SIDEBAR LOGIC ---
if st.sidebar.button("♻️ Refresh Data Sources"):
    st.cache_data.clear()
    st.success("Cache cleared!")

# --- HEADER & SEARCH ---
st.title("Injection Trial Data Entry")
st.subheader("Search Project Tracker")

col_s1, col_s2 = st.columns([1, 3])
with col_s1:
    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")
with col_s2:
    st.write("##") 
    if st.button("Pull Information"):
        if search_input:
            data = get_project_data(search_input)
            if data:
                st.session_state.lookup_data = data
                st.success(f"Project details loaded for {search_input}")
            else:
                st.warning("No project data found.")
                st.session_state.lookup_data = {}

st.divider()

# --- MAIN LOGIC (Only runs if search_input is provided) ---
if search_input:
    # 1. Trial History & Sync
    st.subheader(f"Trial Timeline: {search_input}")
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")
    with col_h2:
        if st.button("🔄 Sync Master Tracker"):
            success, msg = sync_last_trial_to_cloud(search_input)
            if success:
                st.success("Master Tracker updated!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Sync failed: {msg}")

    display_trial_history(search_input)
    st.divider()

    # 2. Success & PDF Download Section
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        if 'last_submission_data' in st.session_state:
            try:
                pdf_bytes = create_pdf(st.session_state.last_submission_data)
                st.download_button(
                    label="📥 Download Trial Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",
                    mime="application/pdf",
                    key="download_pdf_main"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
        
        if st.button("Start Next Entry"):
            st.session_state.submitted = False 
            if 'last_submission_data' in st.session_state:
                del st.session_state.last_submission_data
            st.rerun()
        st.divider()

    # 3. New Trial Entry Form
    ld = st.session_state.get('lookup_data', {})
    current_trial_ref = get_next_trial_reference(search_input)

    with st.form("injection_xlsm_form", clear_on_submit=True):
        st.subheader(f"New Trial Entry: {current_trial_ref}")
        
        # Form Sections
        st.subheader("1. Sales & Administration")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            trial_date = st.date_input("Date", datetime.now())
            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))
        with s2:
            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)
            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)
            target_to = st.text_input("Target to", value=ld.get('Target to', ''))
        with s3:
            client = st.text_input("Client", value=ld.get('Client', ''))
            trial_qty = st.number_input("Trial Quantity", step=1)
        with s4:
            operator = st.text_input("Operator")
            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))
            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))

        st.divider()
        st.subheader("2. Product Specifications")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            description = st.text_input("Description", value=ld.get('Project Description', ''))
            length = st.text_input("Length", value=str(ld.get('Length', '')))
            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))
            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))
        with p2:
            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))
            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))
            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))
            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))
        with p3:
            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))
            material = st.text_input("Material", value=ld.get('Material', ''))
            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))
            pre_mix_perc = st.text_input("Pre-mix %", value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))
        with p4:
            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)
            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)
            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)

        st.divider()
        st.subheader("3. Dosing Unit Settings")
        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))
        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))
        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))
        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))
        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))

        st.divider()
        st.subheader("4. Machine Process Settings")
        pr1, pr2, pr3, pr4 = st.columns(4)
        with pr1:
            inj_p = st.number_input("Injection Pressure (bar)", step=1)
            hold_p = st.number_input("Holding Pressure (bar)", step=1)
        with pr2:
            inj_s = st.number_input("Injection Speed (mm/s)", step=1)
            back_p = st.number_input("Back Pressure (bar)", step=1)
        with pr3:
            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")
            cool_t = st.number_input("Cooling Time (s)", format="%.2f")
        with pr4:
            dos_s = st.number_input("Dosage Stroke (mm)", step=1)
            dec_m = st.number_input("Decompression (mm)", step=1)

        st.divider()
        st.subheader("5. Trial Observations")
        notes = st.text_area("Observations")

        submit_trial = st.form_submit_button("Submit Trial Entry")

        if submit_trial:
            with st.status("Saving Data...", expanded=True) as status:
                st.write("📝 Writing to trial history...")
                new_submission = {
                    "Trial Ref": current_trial_ref,
                    "Pre-Prod No.": str(search_input),
                    "Date": trial_date.strftime("%Y-%m-%d"),
                    "Sales Rep": sales_rep,
                    "Client": client,
                    "Operator": operator,
                    "Observations": notes,
                    "Cycle Time": cyc_t,
                    "Inj Pressure": inj_p,
                    "Tinuvin": tinuvin_val,
                    "Dosing Unit Fitted": dosing_fitted,
                    "Dosing Calibrated": dosing_calib,
                    "Colour Set": colour_set,
                    "Shot Weight": shot_w
                }
                
                # Save Data Logic
                st.session_state.last_submission_data = {
                    "Trial Reference": current_trial_ref,
                    "Pre-Prod No.": search_input,
                    "Date": trial_date.strftime("%Y-%m-%d"),
                    "Client": client,
                    "Operator": operator,
                    "Cycle Time": f"{cyc_t}s",
                    "Inj Pressure": f"{inj_p} bar",
                    "Observations": notes
                }

                # Parquet Save
                df_new = pd.DataFrame([new_submission])
                if os.path.exists(SUBMISSIONS_FILE):
                    df_existing = pd.read_parquet(SUBMISSIONS_FILE)
                    df_final = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df_final = df_new
                df_final.to_parquet(SUBMISSIONS_FILE, index=False)

                # Local Tracker Update
                if os.path.exists(FILENAME_PARQUET):
                    df_tracker = pd.read_parquet(FILENAME_PARQUET)
                    search_id = str(search_input).zfill(5)
                    trial_suffix = current_trial_ref.split('_')[-1]
                    combined_val = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"
                    mask = df_tracker['Pre-Prod No.'].astype(str).str.zfill(5) == search_id
                    if mask.any():
                        df_tracker.loc[mask, 'Injection trial requested'] = combined_val
                        df_tracker.to_parquet(FILENAME_PARQUET, index=False)

                # Cloud Sync
                success, msg = update_tracker_status(search_input, current_trial_ref)
                if success:
                    st.session_state.submitted = True
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Cloud Sync Failed: {msg}")
streamlit.errors.StreamlitDuplicateElementId: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/injectiontrial/InjectionTrial.py", line 385, in <module>

if st.button("Start Next Entry"):

~~~~~~~~~^^^^^^^^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 563, in wrapped_func

result = non_optional_func(*args, **kwargs)

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 379, in button

return self.dg._button(

~~~~~~~~~~~~~~~^

label,

^^^^^^

...<12 lines>...

shortcut=shortcut,

^^^^^^^^^^^^^^^^^^

)

^

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 1648, in _button

element_id = compute_and_register_element_id(

"form_submit_button" if is_form_submitter else "button",

...<10 lines>...

shortcut=normalized_shortcut,

)

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 265, in compute_and_register_element_id

_register_element_id(ctx, element_type, element_id)

~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 150, in _register_element_id

raise StreamlitDuplicateElementId(element_type)

This error, StreamlitDuplicateElementId, is happening because you now have two "Start Next Entry" buttons with the exact same label. Streamlit uses the label of a button to create a unique ID; if it sees two buttons named the same thing, it crashes because it doesn't know which one the user clicked.

In the previous cleanup, a "Start Next Entry" button remained inside the Success & PDF Section and another was accidentally left at the very bottom in the UI Feedback and Reset section.

The Fix
You need to remove the duplicate block at the very bottom of your script. Here is the corrected logic for the end of your file.

1. Locate this block at the very bottom of your script and DELETE it:

Python
# DELETE THIS ENTIRE SECTION AT THE BOTTOM
if st.session_state.get('submitted', False):
    st.success("Entry Saved Successfully!")
    if st.button("Start Next Entry"):
        st.session_state.lookup_data = {}
        st.session_state.submitted = False 
        st.rerun()
2. Ensure your "Success & PDF Section" (middle of the script) looks like this:
This section handles everything once. Note that I've added a unique key to the button just to be extra safe.

Python
    # --- 2. SUCCESS & PDF SECTION ---
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        
        if 'last_submission_data' in st.session_state:
            try:
                pdf_bytes = create_pdf(st.session_state.last_submission_data)
                st.download_button(
                    label="📥 Download Trial Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",
                    mime="application/pdf",
                    key="download_pdf_main" # Unique key
                )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
        
        # This is your ONE AND ONLY "Start Next Entry" button
        if st.button("Start Next Entry", key="btn_next_entry_main"):
            st.session_state.submitted = False 
            st.session_state.lookup_data = {} # Clear the lookup data for the next one
            if 'last_submission_data' in st.session_state:
                del st.session_state.last_submission_data
            st.rerun()
            
        st.divider() 
Why this happens
Streamlit renders the page from top to bottom every time something changes. If your code path hits two lines that both say st.button("Start Next Entry"), it tries to register two widgets with the same ID. By keeping the button inside the if search_input: and if submitted: logic blocks and ensuring it only appears once in the code, the error will vanish.

Error when saving: streamlit.errors.StreamlitDuplicateElementId: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/injectiontrial/InjectionTrial.py", line 385, in <module>

if st.button("Start Next Entry"):

~~~~~~~~~^^^^^^^^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 563, in wrapped_func

result = non_optional_func(*args, **kwargs)

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 379, in button

return self.dg._button(

~~~~~~~~~~~~~~~^

label,

^^^^^^

...<12 lines>...

shortcut=shortcut,

^^^^^^^^^^^^^^^^^^

)

^

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 1648, in _button

element_id = compute_and_register_element_id(

"form_submit_button" if is_form_submitter else "button",

...<10 lines>...

shortcut=normalized_shortcut,

)

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 265, in compute_and_register_element_id

_register_element_id(ctx, element_type, element_id)

~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 150, in _register_element_id

raise StreamlitDuplicateElementId(element_type) Here is the Injection trial request code: import streamlit as st

import pandas as pd

from datetime import datetime

import os

import time

from fpdf import FPDF

import io



# --- PAGE CONFIGURATION ---

st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")



# ---- CONFIGURATION

TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"



# --- DIRECTORY SETUP ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")



# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1)

                            st.rerun()

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    import gspread

    from google.oauth2.service_account import Credentials



    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row

        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, "No history file found."

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        project_history['Trial_Num'] = project_history['Trial Ref'].str.extract(r'(\d+)$').astype(int)

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(pre_prod_no, latest_trial['Trial Ref'], manual_date=latest_trial['Date'])

    except Exception as e:

        return False, str(e)



def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for key, value in data.items():

        pdf.set_font("Arial", "B", 11)

        pdf.cell(50, 10, txt=f"{key}:", border=0)

        pdf.set_font("Arial", size=11)

        pdf.cell(0, 10, txt=f"{str(value)}", border=0, ln=True)

    return pdf.output(dest='S').encode('latin-1')



# --- INITIALIZE SESSION STATE ---

if 'lookup_data' not in st.session_state:

    st.session_state.lookup_data = {}

if 'submitted' not in st.session_state:

    st.session_state.submitted = False



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared!")



# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- MAIN LOGIC (Only runs if search_input is provided) ---

if search_input:

    # 1. Trial History & Sync

    st.subheader(f"Trial Timeline: {search_input}")

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    display_trial_history(search_input)

    st.divider()



    # 2. Success & PDF Download Section

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf_main"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()

        st.divider()



    # 3. New Trial Entry Form

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        # Form Sections

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()

        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("Pre-mix %", value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()

        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()

        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



        if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                st.write("📝 Writing to trial history...")

                new_submission = {

                    "Trial Ref": current_trial_ref,

                    "Pre-Prod No.": str(search_input),

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": sales_rep,

                    "Client": client,

                    "Operator": operator,

                    "Observations": notes,

                    "Cycle Time": cyc_t,

                    "Inj Pressure": inj_p,

                    "Tinuvin": tinuvin_val,

                    "Dosing Unit Fitted": dosing_fitted,

                    "Dosing Calibrated": dosing_calib,

                    "Colour Set": colour_set,

                    "Shot Weight": shot_w

                }

               

                # Save Data Logic

                st.session_state.last_submission_data = {

                    "Trial Reference": current_trial_ref,

                    "Pre-Prod No.": search_input,

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Client": client,

                    "Operator": operator,

                    "Cycle Time": f"{cyc_t}s",

                    "Inj Pressure": f"{inj_p} bar",

                    "Observations": notes

                }



                # Parquet Save

                df_new = pd.DataFrame([new_submission])

                if os.path.exists(SUBMISSIONS_FILE):

                    df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                    df_final = pd.concat([df_existing, df_new], ignore_index=True)

                else:

                    df_final = df_new

                df_final.to_parquet(SUBMISSIONS_FILE, index=False)



                # Local Tracker Update

                if os.path.exists(FILENAME_PARQUET):

                    df_tracker = pd.read_parquet(FILENAME_PARQUET)

                    search_id = str(search_input).zfill(5)

                    trial_suffix = current_trial_ref.split('_')[-1]

                    combined_val = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"

                    mask = df_tracker['Pre-Prod No.'].astype(str).str.zfill(5) == search_id

                    if mask.any():

                        df_tracker.loc[mask, 'Injection trial requested'] = combined_val

                        df_tracker.to_parquet(FILENAME_PARQUET, index=False)



                # Cloud Sync

                success, msg = update_tracker_status(search_input, current_trial_ref)

                if success:

                    st.session_state.submitted = True

                    st.cache_data.clear()

                    st.rerun()

                else:

                    st.error(f"Cloud Sync Failed: {msg}")



    # UI Feedback and Reset

    if st.session_state.get('submitted', False):

        st.success("Entry Saved Successfully!")

        if st.button("Start Next Entry"):

            st.session_state.lookup_data = {}

            st.session_state.submitted = False

            st.rerun()

The error occurs because you have two separate code blocks creating a button labeled "Start Next Entry".

In Streamlit, every widget needs a unique internal ID. By default, Streamlit derives this ID from the label string. Since your code has two identical buttons, the second one attempted to register itself with an ID that was already taken by the first, causing the StreamlitDuplicateElementId crash.

The Fix
You need to consolidate your logic so that the "Start Next Entry" button only appears once, or provide them with unique keys. Since you already have a "Success & PDF" section in the middle of your script, the section at the very bottom is redundant and causing the conflict.

1. Remove the duplicate block at the end of your file.
Delete these lines (approx. lines 384–389):

Python
# DELETE THIS SECTION AT THE VERY BOTTOM OF YOUR SCRIPT
if st.session_state.get('submitted', False):
    st.success("Entry Saved Successfully!")
    if st.button("Start Next Entry"):
        st.session_state.lookup_data = {}
        st.session_state.submitted = False 
        st.rerun()
2. Update your existing Success Section (Middle of the script).
Ensure the section starting around line 188 looks like this. I have added a unique key to the button to ensure there is never a conflict:

Python
    # --- 2. Success & PDF Download Section ---
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        if 'last_submission_data' in st.session_state:
            try:
                pdf_bytes = create_pdf(st.session_state.last_submission_data)
                st.download_button(
                    label="📥 Download Trial Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",
                    mime="application/pdf",
                    key="download_pdf_main"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
        
        # Use a unique 'key' here to prevent any ID collisions
        if st.button("Start Next Entry", key="btn_next_entry_reset"):
            st.session_state.submitted = False 
            st.session_state.lookup_data = {} # Added this to clear previous search data
            if 'last_submission_data' in st.session_state:
                del st.session_state.last_submission_data
            st.rerun()
        st.divider()
Why this happens in your specific script:
Streamlit scripts run from top to bottom.

The script enters the if search_input: block.

If submitted is True, it renders the first "Start Next Entry" button (Line ~206).

The script finishes the form block and then reaches the bottom of the script.

It sees if st.session_state.get('submitted', False): again and tries to render a second button with the same name (Line ~386). CRASH.

By removing the bottom block and keeping the reset logic inside the main "Success" area, your app will run smoothly.

Is it possible to create the google spreadsheet column headings from the descriptions in this code so that I do not have to retype them: import streamlit as st

import pandas as pd

from datetime import datetime

import os

import time

from fpdf import FPDF

import io



# --- PAGE CONFIGURATION ---

st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")



# ---- CONFIGURATION

TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"



# --- DIRECTORY SETUP ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")



# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        # Convert to string to ensure filtering works correctly

        df['Pre-Prod No.'] = df['Pre-Prod No.'].astype(str)

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    # FIX: Added 'index' to the key to guarantee uniqueness

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}_{index}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1)

                            st.rerun()

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    import gspread

    from google.oauth2.service_account import Credentials



    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row

        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, "No history file found."

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

       

        # 1. Clean data: Ensure Pre-Prod No. is a string and drop rows where Trial Ref is missing

        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)

        df_history = df_history.dropna(subset=['Trial Ref'])

       

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        # 2. Extract number safely: fill NaN with 0 before converting to int

        project_history['Trial_Num'] = (

            project_history['Trial Ref']

            .str.extract(r'(\d+)$')

            .fillna(0) # If no number found, use 0

            .astype(int)

        )

       

        # 3. Get the latest entry

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(pre_prod_no, latest_trial['Trial Ref'], manual_date=latest_trial['Date'])

    except Exception as e:

        return False, f"Sync Logic Error: {str(e)}"



def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

   

    # Title

    pdf.set_font("Arial", "B", 18)

    pdf.cell(0, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.set_draw_color(50, 50, 50)

    pdf.line(10, 22, 200, 22)

    pdf.ln(10)



    def add_section(title):

        pdf.set_font("Arial", "B", 12)

        pdf.set_fill_color(230, 230, 230)

        pdf.cell(0, 8, txt=f" {title}", ln=True, fill=True)

        pdf.ln(2)



    def add_row(label, value, label2="", value2=""):

        pdf.set_font("Arial", "B", 10)

        pdf.cell(45, 7, txt=f"{label}:", border=0)

        pdf.set_font("Arial", size=10)

        pdf.cell(50, 7, txt=f"{str(value)}", border=0)

       

        if label2:

            pdf.set_font("Arial", "B", 10)

            pdf.cell(45, 7, txt=f"{label2}:", border=0)

            pdf.set_font("Arial", size=10)

            pdf.cell(0, 7, txt=f"{str(value2)}", border=0)

        pdf.ln(7)



    # Section 1: Admin

    add_section("1. Sales & Administration")

    add_row("Trial Ref", data.get("Trial Reference"), "Date", data.get("Date"))

    add_row("Pre-Prod No.", data.get("Pre-Prod No."), "Sales Rep", data.get("Sales Rep"))

    add_row("Client", data.get("Client"), "Target To", data.get("Target to"))

    add_row("Operator", data.get("Operator"), "Trial Qty", data.get("Trial Quantity"))

    add_row("Prod Machine", data.get("Production Machine"), "Trial Machine", data.get("Trial Machine"))

    pdf.ln(5)



    # Section 2: Product Specs

    add_section("2. Product Specifications")

   

    # --- DESCRIPTION (Special wrap-around handling) ---

    pdf.set_font("Arial", "B", 10)

    pdf.cell(45, 7, txt="Description:", border=0)

    pdf.set_font("Arial", size=10)

    # Using multi_cell for wrap-around. 0 means extend to right margin.

    pdf.multi_cell(0, 7, txt=str(data.get("Description", "")))

   

    # Continue with other rows

    add_row("Product Code", data.get("Product Code"), "Material", data.get("Material"))

    add_row("Supplier", data.get("Supplier"), "Cap/Lid Style", data.get("Cap_Lid Style"))

    add_row("Cap/Lid Material", data.get("Cap_Lid Material"), "Diameter", data.get("Diameter"))

    add_row("Length", data.get("Length"), "Orifice", data.get("Orifice"))

    add_row("Mix %", data.get("Mix_%"), "Pigment Grade", data.get("Pigment_MB Grade"))

    add_row("Pre-mix %", data.get("Pre-mix %"), "Tinuvin", data.get("Tinuvin"))

    add_row("Dosing Fitted", data.get("Dosing Unit Fitted"), "Dosing Calib", data.get("Dosing Calibrated"))

    pdf.ln(5)



    # Section 3 & 4: Settings

    add_section("3. Dosing & 4. Process Settings")

    add_row("Colour Set", data.get("Colour Set"), "Colour Actual", data.get("Colour Actual"))

    add_row("Shot Weight", data.get("Shot Weight"), "Dosing Time", data.get("Dosing Time"))

    add_row("Inj Pressure", data.get("Inj Pressure"), "Hold Pressure", data.get("Holding Pressure"))

    add_row("Inj Speed", data.get("Injection Speed"), "Back Pressure", data.get("Back Pressure"))

    add_row("Cycle Time", data.get("Cycle Time"), "Cooling Time", data.get("Cooling Time"))

    pdf.ln(5)



    # Section 5: Observations

    add_section("5. Trial Observations")

    pdf.set_font("Arial", size=10)

    pdf.multi_cell(0, 7, txt=str(data.get("Observations", "")))



    return pdf.output(dest='S').encode('latin-1')



# --- INITIALIZE SESSION STATE ---

if 'lookup_data' not in st.session_state:

    st.session_state.lookup_data = {}

if 'submitted' not in st.session_state:

    st.session_state.submitted = False



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared!")



# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- MAIN LOGIC (Only runs if search_input is provided) ---

if search_input:

    # 1. Trial History & Sync

    st.subheader(f"Trial Timeline: {search_input}")

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    display_trial_history(search_input)

    st.divider()



    # 2. Success & PDF Download Section

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf_main"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()

        st.divider()



    # 3. New Trial Entry Form

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        # Form Sections

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()

        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("Pre-mix %", value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()

        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()

        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



    if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                # Create the full dictionary for the PDF and Parquet

                full_data = {

                    "Trial Reference": current_trial_ref,

                    "Pre-Prod No.": str(search_input), # Force string

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": str(sales_rep),

                    "Target to": str(target_to),

                    "Client": str(client),

                    "Trial Quantity": str(trial_qty),

                    "Operator": str(operator),

                    "Production Machine": str(machine_prod),

                    "Trial Machine": str(machine_trial),

                    "Description": str(description),

                    "Length": str(length),

                    "Orifice": str(orifice),

                    "Supplier": str(supplier),

                    "Cap_Lid Style": str(cap_lid_style),

                    "Cap_Lid Material": str(cap_lid_material),

                    "Diameter": str(cap_lid_diameter),

                    "Mix_%": str(mix),

                    "Product Code": str(product_code),

                    "Material": str(material),

                    "Pigment_MB Grade": str(pigment),

                    "Pre-mix %": str(pre_mix_perc),

                    "Tinuvin": str(tinuvin_val),

                    "Dosing Unit Fitted": str(dosing_fitted),

                    "Dosing Calibrated": str(dosing_calib),

                    "Colour Set": str(colour_set),

                    "Colour Actual": str(colour_act),

                    "Colour Percentage": str(colour_perc),

                    "Shot Weight": str(shot_w),

                    "Dosing Time": str(dosing_time),

                    "Inj Pressure": f"{inj_p} bar",

                    "Holding Pressure": f"{hold_p} bar",

                    "Injection Speed": f"{inj_s} mm/s",

                    "Back Pressure": f"{back_p} bar",

                    "Cycle Time": f"{cyc_t}s",

                    "Cooling Time": f"{cool_t}s",

                    "Dosage Stroke": str(dos_s),

                    "Decompression": str(dec_m),

                    "Observations": str(notes)

                }

               

                st.session_state.last_submission_data = full_data



                # Parquet Save Logic with Type Safety

                df_new = pd.DataFrame([full_data])

               

                if os.path.exists(SUBMISSIONS_FILE):

                    try:

                        df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                        # Ensure both dataframes have identical column types (Strings) to prevent Arrow errors

                        df_existing = df_existing.astype(str)

                        df_new = df_new.astype(str)

                        df_final = pd.concat([df_existing, df_new], ignore_index=True)

                    except Exception as e:

                        st.warning(f"Existing file schema mismatch. Starting fresh: {e}")

                        df_final = df_new

                else:

                    df_final = df_new



                # FINAL STEP: Ensure everything is string before writing to Parquet

                df_final = df_final.astype(str)

                df_final.to_parquet(SUBMISSIONS_FILE, index=False, engine='pyarrow')



                # Cloud Sync

                success, msg = update_tracker_status(search_input, current_trial_ref)

                if success:

                    st.session_state.submitted = True

                    st.cache_data.clear()

                    st.rerun()

                else:

                    st.error(f"Cloud Sync Failed: {msg}")    

Yes, it is definitely possible. Since you have already mapped out all your data points in the full_data dictionary within your submission logic, we can create a script that extracts those keys and writes them as the first row (the header) of a new Google Sheet.

You can run this once as a "setup" script to initialize your spreadsheet.

The Setup Script
This script will connect to your Google Sheet, check if it's empty, and if so, write the headers derived directly from your code.

Python
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- SETTINGS ---
TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"

def initialize_google_sheet_headers():
    # 1. Define the exact keys from your 'full_data' dictionary
    # This ensures your Spreadsheet matches your Python code perfectly
    headers = [
        "Trial Reference", "Pre-Prod No.", "Date", "Sales Rep", "Target to",
        "Client", "Trial Quantity", "Operator", "Production Machine",
        "Trial Machine", "Description", "Length", "Orifice", "Supplier",
        "Cap_Lid Style", "Cap_Lid Material", "Diameter", "Mix_%",
        "Product Code", "Material", "Pigment_MB Grade", "Pre-mix %",
        "Tinuvin", "Dosing Unit Fitted", "Dosing Calibrated", "Colour Set",
        "Colour Actual", "Colour Percentage", "Shot Weight", "Dosing Time",
        "Inj Pressure", "Holding Pressure", "Injection Speed", "Back Pressure",
        "Cycle Time", "Cooling Time", "Dosage Stroke", "Decompression",
        "Observations"
    ]

    try:
        # 2. Authentication (using your existing secrets logic)
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]
        
        if isinstance(creds_info, dict) and "private_key" in creds_info:
             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # 3. Open the sheet
        spreadsheet = client.open_by_key(TRACKER_FILE_ID)
        worksheet = spreadsheet.get_worksheet(0) # Targets the first tab

        # 4. Check if the first cell is empty before writing to avoid overwriting data
        if not worksheet.acell('A1').value:
            worksheet.insert_row(headers, 1)
            st.success("✅ Headers created successfully in Google Sheets!")
        else:
            st.warning("⚠️ Sheet already has data in the first row. No headers were added.")

    except Exception as e:
        st.error(f"Failed to create headers: {e}")

# To run this, you could add a button in your Sidebar temporarily:
if st.sidebar.button("🛠️ Initialize GSHEET Headers"):
    initialize_google_sheet_headers()
Why this is better:
Consistency: The column names in your spreadsheet will be character-for-character identical to the keys you use in full_data. This prevents errors when you try to pull or sync data later.

Efficiency: You don't have to manually create 39 columns in the Google Sheets UI.

Safety: The script checks if not worksheet.acell('A1').value, so it won't accidentally wipe out your headers if you click the button twice.

How to use it:
Paste the function above into your main app file (or a separate management script).

Run the app and click the Initialize GSHEET Headers button in the sidebar once.

Once the "Success" message appears, you can delete the button code or comment it out.

can i save the python file as InjectionTrialSheet.py

Yes, you absolutely can rename the file to InjectionTrialSheet.py.

However, because your code relies on file paths and environment settings, there are three specific things you need to check to make sure the app doesn't break after the rename:

1. Update the GitHub / Streamlit Cloud Path
If you are hosting this on Streamlit Cloud, the platform looks for a specific filename to launch the app.

Go to your Streamlit Cloud Dashboard.

Click Manage App > Settings.

Update the Main file path from InjectionTrial.py to InjectionTrialSheet.py.

If you don't do this, the app will show a "File not found" error.

2. Check internal path references
In the code you provided, you are using os.path.abspath(__file__) to find your data files:

Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
This is the correct way to do it! Because you used this dynamic method, the app will automatically know where it is even after the name change. You won't need to change any of your FILENAME_PARQUET or SUBMISSIONS_FILE logic.

3. Local Terminal Execution
If you run the app locally on your computer, remember to change your startup command in the terminal:

Old command: streamlit run InjectionTrial.py

New command: streamlit run InjectionTrialSheet.py

Quick Tip: If you have any other python files in the same folder that import InjectionTrial, those will break until you update the import statement to import InjectionTrialSheet. If this is your only file, you’re all set!

when you state 'Main app file', do you mean under the import section but above PAGE CONFIGURATION in InjectionTrial.py

In Python, the order of code matters because the script is read from top to bottom. When adding a new function like the initialize_google_sheet_headers tool I gave you, it's best to place the function definition in the "Helper Functions" area and the button trigger where you want it to appear in the UI.

Here is exactly where to place the pieces in your script:

1. The Function Definition
Place the def initialize_google_sheet_headers(): block under your other helper functions (like create_pdf or update_tracker_status).

It should be above the section where you initialize the session state.

Python
# ... (existing helper functions like create_pdf)

def initialize_google_sheet_headers():
    # ... (the code I provided in the previous response)
    pass

# --- INITIALIZE SESSION STATE --- (Keep this below the functions)
if 'lookup_data' not in st.session_state:
    # ...
2. The Button Trigger
Place the button code inside your Sidebar Logic section. This ensures the button appears on the left-hand side of your app, keeping the main screen clean for data entry.

Look for this section in your script (around line 170):

Python
# --- SIDEBAR LOGIC ---
if st.sidebar.button("♻️ Refresh Data Sources"):
    st.cache_data.clear()
    st.success("Cache cleared!")

# ADD THE NEW BUTTON DIRECTLY BELOW IT:
if st.sidebar.button("🛠️ Initialize GSHEET Headers"):
    initialize_google_sheet_headers()
Summary of the Structure
To keep your code professional and readable, follow this "top-to-bottom" flow:

Imports: import streamlit, import pandas, etc.

Configuration/Paths: TRACKER_FILE_ID, BASE_DIR.

Helper Functions: All your def blocks (where you put the new logic).

Session State Initialization: Setting up st.session_state.

Sidebar UI: Where the buttons live.

Main Page UI: Titles, Search bars, and the Form.

Note: If you have already renamed your file to InjectionTrialSheet.py, just make sure you are editing that specific file!

what is the path to google to create a google spreadsheet toml

To create a TOML (Tom's Obvious, Minimal Language) configuration for Google Sheets—which is exactly what Streamlit uses to connect to your data—you need to follow the path through the Google Cloud Console.

The "path" isn't a single URL, but a series of steps to generate a Service Account Key.

1. The Path in Google Cloud Console
Go to the Google Cloud Console.

Create a Project (or select your existing "InjectionTrial" project).

Search for "Google Sheets API" in the top search bar and click Enable. Repeat this for the "Google Drive API".

Navigate to IAM & Admin > Service Accounts.

Click Create Service Account, give it a name (e.g., "streamlit-access"), and click Create and Continue.

Assign the role Basic > Editor and click Done.

Click on the newly created email address in the list, go to the Keys tab, click Add Key > Create New Key, and select JSON.

2. Converting JSON to TOML
Google will download a .json file to your computer. Streamlit needs this information in a specific TOML format inside your .streamlit/secrets.toml file (for local use) or the "Secrets" field on Streamlit Cloud.

Your TOML structure should look like this:

Ini, TOML
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYourKeyHere\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account-email@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
3. The "Missing" Final Step
The most common reason for errors isn't the TOML file—it's the permissions.

You must take the client_email found in your TOML/JSON file and go to your actual Google Spreadsheet, click the "Share" button, and paste that email address as an "Editor." Without this, your Python code will have the right keys but won't be allowed through the door of that specific spreadsheet.

Summary of the "Path"
Google Cloud Console → Enable APIs → Create Service Account → Download JSON Key → Convert to TOML → Share Spreadsheet with Service Email.

I have created a new toml for the google spreadsheet called 'Trial Timeline' which will contain all the information to do with the Injection trials. I was using the ProjectTracker secrets key because I hadn't intended retaining the historical data of the trials on a spreadsheet. I need the code that is between def initialize_google_sheet_headers():

# ... (the code I provided in the previous response)

pass# --- INITIALIZE SESSION STATE --- (Keep this below the functions)if 'lookup_data' not in st.session_state:

# ... to create all the headers on the Google spreadsheet to be adjusted accordingly: import streamlit as st

import pandas as pd

from datetime import datetime

import os

import time

from fpdf import FPDF

import io



# --- PAGE CONFIGURATION ---

st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")



# ---- CONFIGURATION

TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"



# --- DIRECTORY SETUP ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")



# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        # Convert to string to ensure filtering works correctly

        df['Pre-Prod No.'] = df['Pre-Prod No.'].astype(str)

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    # FIX: Added 'index' to the key to guarantee uniqueness

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}_{index}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1)

                            st.rerun()

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    import gspread

    from google.oauth2.service_account import Credentials



    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

        row_idx = cell.row

        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, "No history file found."

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

       

        # 1. Clean data: Ensure Pre-Prod No. is a string and drop rows where Trial Ref is missing

        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)

        df_history = df_history.dropna(subset=['Trial Ref'])

       

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        # 2. Extract number safely: fill NaN with 0 before converting to int

        project_history['Trial_Num'] = (

            project_history['Trial Ref']

            .str.extract(r'(\d+)$')

            .fillna(0) # If no number found, use 0

            .astype(int)

        )

       

        # 3. Get the latest entry

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(pre_prod_no, latest_trial['Trial Ref'], manual_date=latest_trial['Date'])

    except Exception as e:

        return False, f"Sync Logic Error: {str(e)}"



def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

   

    # Title

    pdf.set_font("Arial", "B", 18)

    pdf.cell(0, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.set_draw_color(50, 50, 50)

    pdf.line(10, 22, 200, 22)

    pdf.ln(10)



    def add_section(title):

        pdf.set_font("Arial", "B", 12)

        pdf.set_fill_color(230, 230, 230)

        pdf.cell(0, 8, txt=f" {title}", ln=True, fill=True)

        pdf.ln(2)



    def add_row(label, value, label2="", value2=""):

        pdf.set_font("Arial", "B", 10)

        pdf.cell(45, 7, txt=f"{label}:", border=0)

        pdf.set_font("Arial", size=10)

        pdf.cell(50, 7, txt=f"{str(value)}", border=0)

       

        if label2:

            pdf.set_font("Arial", "B", 10)

            pdf.cell(45, 7, txt=f"{label2}:", border=0)

            pdf.set_font("Arial", size=10)

            pdf.cell(0, 7, txt=f"{str(value2)}", border=0)

        pdf.ln(7)



    # Section 1: Admin

    add_section("1. Sales & Administration")

    add_row("Trial Ref", data.get("Trial Reference"), "Date", data.get("Date"))

    add_row("Pre-Prod No.", data.get("Pre-Prod No."), "Sales Rep", data.get("Sales Rep"))

    add_row("Client", data.get("Client"), "Target To", data.get("Target to"))

    add_row("Operator", data.get("Operator"), "Trial Qty", data.get("Trial Quantity"))

    add_row("Prod Machine", data.get("Production Machine"), "Trial Machine", data.get("Trial Machine"))

    pdf.ln(5)



    # Section 2: Product Specs

    add_section("2. Product Specifications")

   

    # --- DESCRIPTION (Special wrap-around handling) ---

    pdf.set_font("Arial", "B", 10)

    pdf.cell(45, 7, txt="Description:", border=0)

    pdf.set_font("Arial", size=10)

    # Using multi_cell for wrap-around. 0 means extend to right margin.

    pdf.multi_cell(0, 7, txt=str(data.get("Description", "")))

   

    # Continue with other rows

    add_row("Product Code", data.get("Product Code"), "Material", data.get("Material"))

    add_row("Supplier", data.get("Supplier"), "Cap/Lid Style", data.get("Cap_Lid Style"))

    add_row("Cap/Lid Material", data.get("Cap_Lid Material"), "Diameter", data.get("Diameter"))

    add_row("Length", data.get("Length"), "Orifice", data.get("Orifice"))

    add_row("Mix %", data.get("Mix_%"), "Pigment Grade", data.get("Pigment_MB Grade"))

    add_row("Pre-mix %", data.get("Pre-mix %"), "Tinuvin", data.get("Tinuvin"))

    add_row("Dosing Fitted", data.get("Dosing Unit Fitted"), "Dosing Calib", data.get("Dosing Calibrated"))

    pdf.ln(5)



    # Section 3 & 4: Settings

    add_section("3. Dosing & 4. Process Settings")

    add_row("Colour Set", data.get("Colour Set"), "Colour Actual", data.get("Colour Actual"))

    add_row("Shot Weight", data.get("Shot Weight"), "Dosing Time", data.get("Dosing Time"))

    add_row("Inj Pressure", data.get("Inj Pressure"), "Hold Pressure", data.get("Holding Pressure"))

    add_row("Inj Speed", data.get("Injection Speed"), "Back Pressure", data.get("Back Pressure"))

    add_row("Cycle Time", data.get("Cycle Time"), "Cooling Time", data.get("Cooling Time"))

    pdf.ln(5)



    # Section 5: Observations

    add_section("5. Trial Observations")

    pdf.set_font("Arial", size=10)

    pdf.multi_cell(0, 7, txt=str(data.get("Observations", "")))



    return pdf.output(dest='S').encode('latin-1')



import streamlit as st

import gspread

from google.oauth2.service_account import Credentials



# --- SETTINGS ---

TRACKER_FILE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"



def initialize_google_sheet_headers():

    # 1. Define the exact keys from your 'full_data' dictionary

    # This ensures your Spreadsheet matches your Python code perfectly

    headers = [

        "Trial Reference", "Pre-Prod No.", "Date", "Sales Rep", "Target to",

        "Client", "Trial Quantity", "Operator", "Production Machine",

        "Trial Machine", "Description", "Length", "Orifice", "Supplier",

        "Cap_Lid Style", "Cap_Lid Material", "Diameter", "Mix_%",

        "Product Code", "Material", "Pigment_MB Grade", "Pre-mix %",

        "Tinuvin", "Dosing Unit Fitted", "Dosing Calibrated", "Colour Set",

        "Colour Actual", "Colour Percentage", "Shot Weight", "Dosing Time",

        "Inj Pressure", "Holding Pressure", "Injection Speed", "Back Pressure",

        "Cycle Time", "Cooling Time", "Dosage Stroke", "Decompression",

        "Observations"

    ]



    try:

        # 2. Authentication (using your existing secrets logic)

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

       

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        # 3. Open the sheet

        spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        worksheet = spreadsheet.get_worksheet(0) # Targets the first tab



        # 4. Check if the first cell is empty before writing to avoid overwriting data

        if not worksheet.acell('A1').value:

            worksheet.insert_row(headers, 1)

            st.success("✅ Headers created successfully in Google Sheets!")

        else:

            st.warning("⚠️ Sheet already has data in the first row. No headers were added.")



    except Exception as e:

        st.error(f"Failed to create headers: {e}")



# To run this, you could add a button in your Sidebar temporarily:

if st.sidebar.button("🛠️ Initialize GSHEET Headers"):

    initialize_google_sheet_headers()



# --- INITIALIZE SESSION STATE ---

if 'lookup_data' not in st.session_state:

    st.session_state.lookup_data = {}

if 'submitted' not in st.session_state:

    st.session_state.submitted = False



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared!")



# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- MAIN LOGIC (Only runs if search_input is provided) ---

if search_input:

    # 1. Trial History & Sync

    st.subheader(f"Trial Timeline: {search_input}")

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    display_trial_history(search_input)

    st.divider()



    # 2. Success & PDF Download Section

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf_main"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()

        st.divider()



    # 3. New Trial Entry Form

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        # Form Sections

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()

        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("Pre-mix %", value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()

        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()

        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



    if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                # Create the full dictionary for the PDF and Parquet

                full_data = {

                    "Trial Reference": current_trial_ref,

                    "Pre-Prod No.": str(search_input), # Force string

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": str(sales_rep),

                    "Target to": str(target_to),

                    "Client": str(client),

                    "Trial Quantity": str(trial_qty),

                    "Operator": str(operator),

                    "Production Machine": str(machine_prod),

                    "Trial Machine": str(machine_trial),

                    "Description": str(description),

                    "Length": str(length),

                    "Orifice": str(orifice),

                    "Supplier": str(supplier),

                    "Cap_Lid Style": str(cap_lid_style),

                    "Cap_Lid Material": str(cap_lid_material),

                    "Diameter": str(cap_lid_diameter),

                    "Mix_%": str(mix),

                    "Product Code": str(product_code),

                    "Material": str(material),

                    "Pigment_MB Grade": str(pigment),

                    "Pre-mix %": str(pre_mix_perc),

                    "Tinuvin": str(tinuvin_val),

                    "Dosing Unit Fitted": str(dosing_fitted),

                    "Dosing Calibrated": str(dosing_calib),

                    "Colour Set": str(colour_set),

                    "Colour Actual": str(colour_act),

                    "Colour Percentage": str(colour_perc),

                    "Shot Weight": str(shot_w),

                    "Dosing Time": str(dosing_time),

                    "Inj Pressure": f"{inj_p} bar",

                    "Holding Pressure": f"{hold_p} bar",

                    "Injection Speed": f"{inj_s} mm/s",

                    "Back Pressure": f"{back_p} bar",

                    "Cycle Time": f"{cyc_t}s",

                    "Cooling Time": f"{cool_t}s",

                    "Dosage Stroke": str(dos_s),

                    "Decompression": str(dec_m),

                    "Observations": str(notes)

                }

               

                st.session_state.last_submission_data = full_data



                # Parquet Save Logic with Type Safety

                df_new = pd.DataFrame([full_data])

               

                if os.path.exists(SUBMISSIONS_FILE):

                    try:

                        df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                        # Ensure both dataframes have identical column types (Strings) to prevent Arrow errors

                        df_existing = df_existing.astype(str)

                        df_new = df_new.astype(str)

                        df_final = pd.concat([df_existing, df_new], ignore_index=True)

                    except Exception as e:

                        st.warning(f"Existing file schema mismatch. Starting fresh: {e}")

                        df_final = df_new

                else:

                    df_final = df_new



                # FINAL STEP: Ensure everything is string before writing to Parquet

                df_final = df_final.astype(str)

                df_final.to_parquet(SUBMISSIONS_FILE, index=False, engine='pyarrow')



                # Cloud Sync

                success, msg = update_tracker_status(search_input, current_trial_ref)

                if success:

                    st.session_state.submitted = True

                    st.cache_data.clear()

                    st.rerun()

                else:

                    st.error(f"Cloud Sync Failed: {msg}")    



I have attached the complete code as reference.

Since you are using a separate Google Sheet for the Trial Timeline, we need to ensure the initialization function uses the correct credentials and targets the new spreadsheet ID you provided.

Here is the updated logic to place in your script between your functions and the session state initialization.

Updated Initialization Logic
Python
# --- GOOGLE SHEETS INITIALIZATION TOOL ---

def initialize_google_sheet_headers():
    """Creates headers in the 'Trial Timeline' spreadsheet if it is empty."""
    
    # These headers are extracted exactly from your 'full_data' dictionary keys
    headers = [
        "Trial Reference", "Pre-Prod No.", "Date", "Sales Rep", "Target to",
        "Client", "Trial Quantity", "Operator", "Production Machine",
        "Trial Machine", "Description", "Length", "Orifice", "Supplier",
        "Cap_Lid Style", "Cap_Lid Material", "Diameter", "Mix_%",
        "Product Code", "Material", "Pigment_MB Grade", "Pre-mix %",
        "Tinuvin", "Dosing Unit Fitted", "Dosing Calibrated", "Colour Set",
        "Colour Actual", "Colour Percentage", "Shot Weight", "Dosing Time",
        "Inj Pressure", "Holding Pressure", "Injection Speed", "Back Pressure",
        "Cycle Time", "Cooling Time", "Dosage Stroke", "Decompression",
        "Observations"
    ]

    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Using the specific secrets key for your Trial Timeline credentials
        # Replace 'trial_timeline_db' with whatever name you gave your new TOML section
        if "trial_timeline_db" in st.secrets:
            creds_info = st.secrets["trial_timeline_db"]
        elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_info = st.secrets["connections"]["gsheets"]
        else:
            creds_info = st.secrets["gcp_service_account"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:
             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Opening the new Trial Timeline Spreadsheet ID
        spreadsheet = client.open_by_key(TRACKER_FILE_ID)
        worksheet = spreadsheet.get_worksheet(0) 

        # Check for existing data
        if not worksheet.acell('A1').value:
            worksheet.insert_row(headers, 1)
            # Optional: Freeze the top row so it stays visible when scrolling
            worksheet.freeze(rows=1)
            st.success("✅ 'Trial Timeline' headers created successfully!")
        else:
            st.warning("⚠️ Sheet already contains data. Headers were not overwritten.")

    except Exception as e:
        st.error(f"Failed to initialize Trial Timeline headers: {e}")

# Trigger button for the sidebar
if st.sidebar.button("🛠️ Setup Trial Timeline Headers"):
    initialize_google_sheet_headers()
Key Changes Made:
Freeze Row: I added worksheet.freeze(rows=1). Since this sheet will be a historical record, freezing the headers makes it much easier to read as the list grows.

Credential Flexibility: I updated the creds_info check to look for a trial_timeline_db key in your secrets. If you named your new TOML section something else, just change that string to match.

Spreadsheet ID: It now correctly uses the new ID you included in your code: 1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y.

One Critical Step:
Since you are now recording every trial on this sheet (instead of just updating a single status cell), you will need to update your update_tracker_status function eventually to use worksheet.append_row() instead of worksheet.update_cell().

Would you like the updated code for the append_row logic to ensure every new trial is saved to its own line in that spreadsheet?

Cloud Sync Failed: 'NoneType' object has no attribute 'row'

This error is occurring because of this specific line in your update_tracker_status function:

Python
cell = tracker_worksheet.find(search_id, in_column=1)
row_idx = cell.row  # <--- Error happens here
The gspread library’s .find() method returns None if it cannot find the value you are looking for. When it returns None, you can't ask for the .row, which leads to the 'NoneType' object has no attribute 'row' crash.

How to Fix It
You need to add a "safety check" to handle cases where the Pre-Prod No. doesn't exist in your Master Tracker.

Replace that section of your update_tracker_status function with this:

Python
        search_id = pad_id(pre_prod_no)
        cell = tracker_worksheet.find(search_id, in_column=1)
        
        # SAFETY CHECK: If cell is None, the ID wasn't found
        if cell is None:
            return False, f"Pre-Prod No. '{search_id}' not found in the Master Tracker spreadsheet."

        row_idx = cell.row
        # ... rest of your code ...
Why is this happening?
There are usually three reasons why the code fails to find the ID:

Leading/Trailing Spaces: If the Google Sheet has " 11925" (with a space) and your app searches for "11925", it won't find it.

Formatting: If the ID in the Google Sheet is formatted as a number (e.g., 11,925.00), gspread might fail to find it if it's searching for the string "11925".

Missing ID: The Pre-Prod number simply hasn't been added to the Master Tracker yet.

A more "Robust" Search (Optional)
If you find that the ID definitely exists but the code still can't find it, you can try searching the entire sheet or using a regular expression, but the Safety Check above is the most important fix to prevent your app from crashing.

File "/mount/src/injectiontrial/InjectionTrial.py", line 360, in <module>

display_trial_history(search_input)

~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^

File "/mount/src/injectiontrial/InjectionTrial.py", line 78, in display_trial_history

st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

~~~^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/series.py", line 959, in __getitem__

return self._get_value(key)

~~~~~~~~~~~~~~~^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/series.py", line 1046, in _get_value

loc = self.index.get_loc(label)

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/indexes/base.py", line 3648, in get_loc

raise KeyError(key) from err: import streamlit as st

import pandas as pd

from datetime import datetime

import os

import time

from fpdf import FPDF

import io



# --- PAGE CONFIGURATION ---

st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")



# ---- CONFIGURATION

TRACKER_FILE_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"



# --- DIRECTORY SETUP ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")



# --- HELPER FUNCTIONS ---



def get_project_data(pre_prod_no):

    """Searches the combined parquet file for the Pre-Prod number."""

    if not os.path.exists(FILENAME_PARQUET):

        st.error(f"Database file not found at: {FILENAME_PARQUET}")

        return None

    try:

        df_tracker = pd.read_parquet(FILENAME_PARQUET)

        col_name = "Pre-Prod No."

        if col_name not in df_tracker.columns:

            st.error(f"Column '{col_name}' not found.")

            return None

        search_term = str(pre_prod_no).strip()

        df_tracker[col_name] = df_tracker[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        result = df_tracker[df_tracker[col_name] == search_term]

        return result.iloc[0].to_dict() if not result.empty else None

    except Exception as e:

        st.error(f"Error reading project database: {e}")

    return None



def get_next_trial_reference(pre_prod_no):

    """Calculates the next trial number by checking submission history."""

    if not os.path.exists(SUBMISSIONS_FILE):

        return f"{pre_prod_no}_T1"

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

        existing_trials = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)]

        count = len(existing_trials)

        return f"{pre_prod_no}_T{count + 1}"

    except:

        return f"{pre_prod_no}_T1"



def delete_trial_entry(trial_ref):

    """Removes a specific trial reference from the submissions file."""

    if os.path.exists(SUBMISSIONS_FILE):

        try:

            df = pd.read_parquet(SUBMISSIONS_FILE)

            df_filtered = df[df['Trial Ref'] != trial_ref]

            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)

            return True

        except Exception as e:

            st.error(f"Error deleting entry: {e}")

            return False

    return False



def display_trial_history(pre_prod_no):

    if os.path.exists(SUBMISSIONS_FILE):

        df = pd.read_parquet(SUBMISSIONS_FILE)

        # Convert to string to ensure filtering works correctly

        df['Pre-Prod No.'] = df['Pre-Prod No.'].astype(str)

        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)

       

        if not history.empty:

            st.info(f"Existing Trials Found: **{len(history)}**")

            for index, row in history.iterrows():

                col1, col2 = st.columns([5, 1])

                with col1:

                    st.write(f"**{row['Trial Ref']}** | {row['Date']} | {row['Operator']}")

                    st.caption(f"Note: {row['Observations']}")

                with col2:

                    # FIX: Added 'index' to the key to guarantee uniqueness

                    if st.button(f"Delete", key=f"del_{row['Trial Ref']}_{index}"):

                        if delete_trial_entry(row['Trial Ref']):

                            st.success(f"Deleted {row['Trial Ref']}")

                            time.sleep(1)

                            st.rerun()

                st.divider()

        else:

            st.write("No previous trial history found.")



def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    import gspread

    from google.oauth2.service_account import Credentials



    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        cell = tracker_worksheet.find(search_id, in_column=1)

       

        # SAFETY CHECK: If cell is None, the ID wasn't found

        if cell is None:

            return False, f"Pre-Prod No. '{search_id}' not found in the Master Tracker spreadsheet."

        row_idx = cell.row

        headers = [h.strip() for h in tracker_worksheet.row_values(1)]

        col_name = "Injection trial requested"

       

        if col_name in headers:

            col_idx = headers.index(col_name) + 1

            tracker_worksheet.update_cell(row_idx, col_idx, combined_value)

            return True, combined_value

        else:

            return False, f"Column '{col_name}' not found."

    except Exception as e:

        return False, str(e)



def sync_last_trial_to_cloud(pre_prod_no):

    if not os.path.exists(SUBMISSIONS_FILE):

        return False, "No history file found."

    try:

        df_history = pd.read_parquet(SUBMISSIONS_FILE)

       

        # 1. Clean data: Ensure Pre-Prod No. is a string and drop rows where Trial Ref is missing

        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)

        df_history = df_history.dropna(subset=['Trial Ref'])

       

        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()

       

        if project_history.empty:

            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials")



        # 2. Extract number safely: fill NaN with 0 before converting to int

        project_history['Trial_Num'] = (

            project_history['Trial Ref']

            .str.extract(r'(\d+)$')

            .fillna(0) # If no number found, use 0

            .astype(int)

        )

       

        # 3. Get the latest entry

        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]

       

        return update_tracker_status(pre_prod_no, latest_trial['Trial Ref'], manual_date=latest_trial['Date'])

    except Exception as e:

        return False, f"Sync Logic Error: {str(e)}"



def create_pdf(data):

    pdf = FPDF()

    pdf.add_page()

   

    # Title

    pdf.set_font("Arial", "B", 18)

    pdf.cell(0, 10, txt="Injection Trial Report", ln=True, align='C')

    pdf.set_draw_color(50, 50, 50)

    pdf.line(10, 22, 200, 22)

    pdf.ln(10)



    def add_section(title):

        pdf.set_font("Arial", "B", 12)

        pdf.set_fill_color(230, 230, 230)

        pdf.cell(0, 8, txt=f" {title}", ln=True, fill=True)

        pdf.ln(2)



    def add_row(label, value, label2="", value2=""):

        pdf.set_font("Arial", "B", 10)

        pdf.cell(45, 7, txt=f"{label}:", border=0)

        pdf.set_font("Arial", size=10)

        pdf.cell(50, 7, txt=f"{str(value)}", border=0)

       

        if label2:

            pdf.set_font("Arial", "B", 10)

            pdf.cell(45, 7, txt=f"{label2}:", border=0)

            pdf.set_font("Arial", size=10)

            pdf.cell(0, 7, txt=f"{str(value2)}", border=0)

        pdf.ln(7)



    # Section 1: Admin

    add_section("1. Sales & Administration")

    add_row("Trial Ref", data.get("Trial Reference"), "Date", data.get("Date"))

    add_row("Pre-Prod No.", data.get("Pre-Prod No."), "Sales Rep", data.get("Sales Rep"))

    add_row("Client", data.get("Client"), "Target To", data.get("Target to"))

    add_row("Operator", data.get("Operator"), "Trial Qty", data.get("Trial Quantity"))

    add_row("Prod Machine", data.get("Production Machine"), "Trial Machine", data.get("Trial Machine"))

    pdf.ln(5)



    # Section 2: Product Specs

    add_section("2. Product Specifications")

   

    # --- DESCRIPTION (Special wrap-around handling) ---

    pdf.set_font("Arial", "B", 10)

    pdf.cell(45, 7, txt="Description:", border=0)

    pdf.set_font("Arial", size=10)

    # Using multi_cell for wrap-around. 0 means extend to right margin.

    pdf.multi_cell(0, 7, txt=str(data.get("Description", "")))

   

    # Continue with other rows

    add_row("Product Code", data.get("Product Code"), "Material", data.get("Material"))

    add_row("Supplier", data.get("Supplier"), "Cap/Lid Style", data.get("Cap_Lid Style"))

    add_row("Cap/Lid Material", data.get("Cap_Lid Material"), "Diameter", data.get("Diameter"))

    add_row("Length", data.get("Length"), "Orifice", data.get("Orifice"))

    add_row("Mix %", data.get("Mix_%"), "Pigment Grade", data.get("Pigment_MB Grade"))

    add_row("Pre-mix %", data.get("Pre-mix %"), "Tinuvin", data.get("Tinuvin"))

    add_row("Dosing Fitted", data.get("Dosing Unit Fitted"), "Dosing Calib", data.get("Dosing Calibrated"))

    pdf.ln(5)



    # Section 3 & 4: Settings

    add_section("3. Dosing & 4. Process Settings")

    add_row("Colour Set", data.get("Colour Set"), "Colour Actual", data.get("Colour Actual"))

    add_row("Shot Weight", data.get("Shot Weight"), "Dosing Time", data.get("Dosing Time"))

    add_row("Inj Pressure", data.get("Inj Pressure"), "Hold Pressure", data.get("Holding Pressure"))

    add_row("Inj Speed", data.get("Injection Speed"), "Back Pressure", data.get("Back Pressure"))

    add_row("Cycle Time", data.get("Cycle Time"), "Cooling Time", data.get("Cooling Time"))

    pdf.ln(5)



    # Section 5: Observations

    add_section("5. Trial Observations")

    pdf.set_font("Arial", size=10)

    pdf.multi_cell(0, 7, txt=str(data.get("Observations", "")))



    return pdf.output(dest='S').encode('latin-1')



import streamlit as st

import gspread

from google.oauth2.service_account import Credentials



# --- SETTINGS ---

TRACKER_FILE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"



# --- GOOGLE SHEETS INITIALIZATION TOOL ---



def initialize_google_sheet_headers():

    """Creates headers in the 'Trial Timeline' spreadsheet if it is empty."""

   

    # These headers are extracted exactly from your 'full_data' dictionary keys

    headers = [

        "Trial Reference", "Pre-Prod No.", "Date", "Sales Rep", "Target to",

        "Client", "Trial Quantity", "Operator", "Production Machine",

        "Trial Machine", "Description", "Length", "Orifice", "Supplier",

        "Cap_Lid Style", "Cap_Lid Material", "Diameter", "Mix_%",

        "Product Code", "Material", "Pigment_MB Grade", "Pre-mix %",

        "Tinuvin", "Dosing Unit Fitted", "Dosing Calibrated", "Colour Set",

        "Colour Actual", "Colour Percentage", "Shot Weight", "Dosing Time",

        "Inj Pressure", "Holding Pressure", "Injection Speed", "Back Pressure",

        "Cycle Time", "Cooling Time", "Dosage Stroke", "Decompression",

        "Observations"

    ]



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

       

        # Using the specific secrets key for your Trial Timeline credentials

        # Replace 'trial_timeline_db' with whatever name you gave your new TOML section

        if "trial_timeline_db" in st.secrets:

            creds_info = st.secrets["trial_timeline_db"]

        elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:

            creds_info = st.secrets["connections"]["gsheets"]

        else:

            creds_info = st.secrets["gcp_service_account"]



        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

       

        # Opening the new Trial Timeline Spreadsheet ID

        spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        worksheet = spreadsheet.get_worksheet(0)



        # Check for existing data

        if not worksheet.acell('A1').value:

            worksheet.insert_row(headers, 1)

            # Optional: Freeze the top row so it stays visible when scrolling

            worksheet.freeze(rows=1)

            st.success("✅ 'Trial Timeline' headers created successfully!")

        else:

            st.warning("⚠️ Sheet already contains data. Headers were not overwritten.")



    except Exception as e:

        st.error(f"Failed to initialize Trial Timeline headers: {e}")



# Trigger button for the sidebar

if st.sidebar.button("🛠️ Setup Trial Timeline Headers"):

    initialize_google_sheet_headers()



# --- INITIALIZE SESSION STATE ---

if 'lookup_data' not in st.session_state:

    st.session_state.lookup_data = {}

if 'submitted' not in st.session_state:

    st.session_state.submitted = False



# --- SIDEBAR LOGIC ---

if st.sidebar.button("♻️ Refresh Data Sources"):

    st.cache_data.clear()

    st.success("Cache cleared!")



# --- HEADER & SEARCH ---

st.title("Injection Trial Data Entry")

st.subheader("Search Project Tracker")



col_s1, col_s2 = st.columns([1, 3])

with col_s1:

    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")

with col_s2:

    st.write("##")

    if st.button("Pull Information"):

        if search_input:

            data = get_project_data(search_input)

            if data:

                st.session_state.lookup_data = data

                st.success(f"Project details loaded for {search_input}")

            else:

                st.warning("No project data found.")

                st.session_state.lookup_data = {}



st.divider()



# --- MAIN LOGIC (Only runs if search_input is provided) ---

if search_input:

    # 1. Trial History & Sync

    st.subheader(f"Trial Timeline: {search_input}")

    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:

        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")

    with col_h2:

        if st.button("🔄 Sync Master Tracker"):

            success, msg = sync_last_trial_to_cloud(search_input)

            if success:

                st.success("Master Tracker updated!")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Sync failed: {msg}")



    display_trial_history(search_input)

    st.divider()



    # 2. Success & PDF Download Section

    if st.session_state.get('submitted', False):

        st.success("🎉 Entry Saved Successfully!")

        if 'last_submission_data' in st.session_state:

            try:

                pdf_bytes = create_pdf(st.session_state.last_submission_data)

                st.download_button(

                    label="📥 Download Trial Report (PDF)",

                    data=pdf_bytes,

                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",

                    mime="application/pdf",

                    key="download_pdf_main"

                )

            except Exception as e:

                st.error(f"Error generating PDF: {e}")

       

        if st.button("Start Next Entry"):

            st.session_state.submitted = False

            if 'last_submission_data' in st.session_state:

                del st.session_state.last_submission_data

            st.rerun()

        st.divider()



    # 3. New Trial Entry Form

    ld = st.session_state.get('lookup_data', {})

    current_trial_ref = get_next_trial_reference(search_input)



    with st.form("injection_xlsm_form", clear_on_submit=True):

        st.subheader(f"New Trial Entry: {current_trial_ref}")

       

        # Form Sections

        st.subheader("1. Sales & Administration")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            trial_date = st.date_input("Date", datetime.now())

            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))

        with s2:

            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)

            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)

            target_to = st.text_input("Target to", value=ld.get('Target to', ''))

        with s3:

            client = st.text_input("Client", value=ld.get('Client', ''))

            trial_qty = st.number_input("Trial Quantity", step=1)

        with s4:

            operator = st.text_input("Operator")

            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))

            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))



        st.divider()

        st.subheader("2. Product Specifications")

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            description = st.text_input("Description", value=ld.get('Project Description', ''))

            length = st.text_input("Length", value=str(ld.get('Length', '')))

            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))

            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))

        with p2:

            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))

            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))

            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))

            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))

        with p3:

            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))

            material = st.text_input("Material", value=ld.get('Material', ''))

            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))

            pre_mix_perc = st.text_input("Pre-mix %", value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))

        with p4:

            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)

            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)

            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)



        st.divider()

        st.subheader("3. Dosing Unit Settings")

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))

        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))

        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))

        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))

        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))



        st.divider()

        st.subheader("4. Machine Process Settings")

        pr1, pr2, pr3, pr4 = st.columns(4)

        with pr1:

            inj_p = st.number_input("Injection Pressure (bar)", step=1)

            hold_p = st.number_input("Holding Pressure (bar)", step=1)

        with pr2:

            inj_s = st.number_input("Injection Speed (mm/s)", step=1)

            back_p = st.number_input("Back Pressure (bar)", step=1)

        with pr3:

            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")

            cool_t = st.number_input("Cooling Time (s)", format="%.2f")

        with pr4:

            dos_s = st.number_input("Dosage Stroke (mm)", step=1)

            dec_m = st.number_input("Decompression (mm)", step=1)



        st.divider()

        st.subheader("5. Trial Observations")

        notes = st.text_area("Observations")



        submit_trial = st.form_submit_button("Submit Trial Entry")



    if submit_trial:

            with st.status("Saving Data...", expanded=True) as status:

                # Create the full dictionary for the PDF and Parquet

                full_data = {

                    "Trial Reference": current_trial_ref,

                    "Pre-Prod No.": str(search_input), # Force string

                    "Date": trial_date.strftime("%Y-%m-%d"),

                    "Sales Rep": str(sales_rep),

                    "Target to": str(target_to),

                    "Client": str(client),

                    "Trial Quantity": str(trial_qty),

                    "Operator": str(operator),

                    "Production Machine": str(machine_prod),

                    "Trial Machine": str(machine_trial),

                    "Description": str(description),

                    "Length": str(length),

                    "Orifice": str(orifice),

                    "Supplier": str(supplier),

                    "Cap_Lid Style": str(cap_lid_style),

                    "Cap_Lid Material": str(cap_lid_material),

                    "Diameter": str(cap_lid_diameter),

                    "Mix_%": str(mix),

                    "Product Code": str(product_code),

                    "Material": str(material),

                    "Pigment_MB Grade": str(pigment),

                    "Pre-mix %": str(pre_mix_perc),

                    "Tinuvin": str(tinuvin_val),

                    "Dosing Unit Fitted": str(dosing_fitted),

                    "Dosing Calibrated": str(dosing_calib),

                    "Colour Set": str(colour_set),

                    "Colour Actual": str(colour_act),

                    "Colour Percentage": str(colour_perc),

                    "Shot Weight": str(shot_w),

                    "Dosing Time": str(dosing_time),

                    "Inj Pressure": f"{inj_p} bar",

                    "Holding Pressure": f"{hold_p} bar",

                    "Injection Speed": f"{inj_s} mm/s",

                    "Back Pressure": f"{back_p} bar",

                    "Cycle Time": f"{cyc_t}s",

                    "Cooling Time": f"{cool_t}s",

                    "Dosage Stroke": str(dos_s),

                    "Decompression": str(dec_m),

                    "Observations": str(notes)

                }

               

                st.session_state.last_submission_data = full_data



                # Parquet Save Logic with Type Safety

                df_new = pd.DataFrame([full_data])

               

                if os.path.exists(SUBMISSIONS_FILE):

                    try:

                        df_existing = pd.read_parquet(SUBMISSIONS_FILE)

                        # Ensure both dataframes have identical column types (Strings) to prevent Arrow errors

                        df_existing = df_existing.astype(str)

                        df_new = df_new.astype(str)

                        df_final = pd.concat([df_existing, df_new], ignore_index=True)

                    except Exception as e:

                        st.warning(f"Existing file schema mismatch. Starting fresh: {e}")

                        df_final = df_new

                else:

                    df_final = df_new



                # FINAL STEP: Ensure everything is string before writing to Parquet

                df_final = df_final.astype(str)

                df_final.to_parquet(SUBMISSIONS_FILE, index=False, engine='pyarrow')



                # Cloud Sync

                success, msg = update_tracker_status(search_input, current_trial_ref)

                if success:

                    st.session_state.submitted = True

                    st.cache_data.clear()

                    st.rerun()

                else:

                    st.error(f"Cloud Sync Failed: {msg}")    

The error KeyError: 'Trial Ref' occurs because the code is looking for a column named "Trial Ref" in your Trial_Submissions.parquet file, but it cannot find it.

Looking at your initialize_google_sheet_headers and full_data dictionary, you named the key "Trial Reference", but inside display_trial_history, you are trying to access row['Trial Ref'].

The Fix
You need to update display_trial_history so the column name matches your data structure exactly.

Update lines 78 and 82–84 in your code:

Python
def display_trial_history(pre_prod_no):
    if os.path.exists(SUBMISSIONS_FILE):
        df = pd.read_parquet(SUBMISSIONS_FILE)
        df['Pre-Prod No.'] = df['Pre-Prod No.'].astype(str)
        history = df[df['Pre-Prod No.'] == str(pre_prod_no)].sort_values('Date', ascending=False)
        
        if not history.empty:
            st.info(f"Existing Trials Found: **{len(history)}**")
            for index, row in history.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    # CHANGE 'Trial Ref' TO 'Trial Reference'
                    st.write(f"**{row['Trial Reference']}** | {row['Date']} | {row['Operator']}")
                    st.caption(f"Note: {row['Observations']}")
                with col2:
                    # CHANGE 'Trial Ref' TO 'Trial Reference'
                    if st.button(f"Delete", key=f"del_{row['Trial Reference']}_{index}"):
                        if delete_trial_entry(row['Trial Reference']):
                            st.success(f"Deleted {row['Trial Reference']}")
                            time.sleep(1) 
                            st.rerun()
                st.divider()
        else:
            st.write("No previous trial history found.")
Why this happened
In your submission logic (line 307), you define:
"Trial Reference": current_trial_ref

However, your display logic was looking for:
row['Trial Ref']

Because Pandas couldn't find a column named exactly "Trial Ref", it raised a KeyError.

A Quick Tip for Future Troubleshooting
If you aren't sure what the column names are in your Parquet file, you can add st.write(df.columns) at the start of your display_trial_history function. It will print out a list of all available headers so you can check for typos or missing columns!

Cloud Sync Failed: Pre-Prod No. '10000' not found in the Master Tracker spreadsheet. should the InjectionTrial.py also include the ProjectTracker.py google spreadsheet toml because all the Pre-Prod No. information is generated on Project tracker

Yes, you should definitely include the Project Tracker credentials in your InjectionTrial.py secrets.

Even though the information is generated by the Project Tracker, the Injection Trial app needs its own "permission slip" (the TOML credentials) to talk to that specific Google Sheet to update the statuses.

Here is how you should structure this to make it work smoothly:

1. Update your .streamlit/secrets.toml
Since your app needs to talk to two different places (or use one set of credentials to access multiple files), ensure your secrets file looks like this. If you are using the same Service Account for both, you can just point to one:

Ini, TOML
# Your existing Master Tracker/General credentials
[connections.gsheets]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://accounts.google.com/o/oauth2/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
2. Verify the Spreadsheet ID
The error message says '10000' not found. This usually happens because:

The ID is wrong: Double-check that TRACKER_FILE_ID in your code (line 120) is the ID for the Project Tracker sheet, not the new Trial Timeline sheet.

Column Mismatch: Ensure the "Pre-Prod No." in the Google Sheet is in Column A (the code uses in_column=1).

3. Adjusting the code for Shared Credentials
In your update_tracker_status function, you are already looking for connections.gsheets. As long as that Service Account has been Shared (via the "Share" button in Google Sheets) with the Project Tracker spreadsheet, it will work.

Checklist for the fix:

Open the Project Tracker Google Sheet.

Click Share.

Paste the client_email found in your secrets (e.g., streamlit-account@your-project.iam.gserviceaccount.com).

Give it Editor permissions.

Why you are seeing "10000 not found"
If you've shared the sheet and the ID is correct, it might be a formatting issue. Google Sheets sometimes treats 10000 as a number, while the app treats it as a string.

You can try changing the search line in your update_tracker_status to be more flexible:

Python
# Change this line:
cell = tracker_worksheet.find(search_id, in_column=1)

# To this (allows it to find the number even if formatted differently):
import re
# Creates a regex that matches the ID exactly
search_re = re.compile(rf"^{search_id}$") 
cell = tracker_worksheet.find(search_re, in_column=1)
Would you like me to show you how to merge both spreadsheet IDs into the sidebar so you can see which one is being updated?

yes, please. I need the information to pull into InjectionTracker from ProjectTracker and then update the 'Injection trial requested' T reference and date in Project Tracker as well as update all the trial details in the 'Trial Timeline' google sheet

To achieve this, you need a dual-client setup in your code. You will use one Spreadsheet ID to pull data (Project Tracker) and a second Spreadsheet ID to save the full trial history (Trial Timeline).

You don't need a second TOML block if the same Service Account has been "Shared" as an Editor on both spreadsheets.

1. Update the Configuration Section
At the top of your script, define both IDs clearly so the code knows which is which.

Python
# --- CONFIGURATION ---
# 1. The Master Project Tracker (where we pull info and update status)
MASTER_TRACKER_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"

# 2. The Trial Timeline (where we save the 39 columns of history)
TRIAL_TIMELINE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"
2. The Updated "Cloud Sync" Logic
Replace your update_tracker_status with this version. It now performs two separate tasks:

Task A: Updates the "T-Ref and Date" in the Project Tracker.

Task B: Appends the full 39-column row to the Trial Timeline.

Python
def update_cloud_databases(pre_prod_no, current_trial_ref, full_data_dict):
    """Handles all Google Sheets updates in one go."""
    import gspread
    from google.oauth2.service_account import Credentials

    # --- 1. SETUP AUTH ---
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]
    if isinstance(creds_info, dict) and "private_key" in creds_info:
         creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)

    try:
        # --- TASK A: UPDATE MASTER PROJECT TRACKER (Status Only) ---
        master_sheet = client.open_by_key(MASTER_TRACKER_ID).get_worksheet(0)
        
        # Clean the ID for searching
        search_id = str(pre_prod_no).strip().split('.')[0]
        cell = master_sheet.find(search_id, in_column=1)
        
        if cell:
            headers = [h.strip() for h in master_sheet.row_values(1)]
            col_name = "Injection trial requested"
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                # Format: T1 - 23/04/2026
                trial_suffix = current_trial_ref.split('_')[-1]
                status_val = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"
                master_sheet.update_cell(cell.row, col_idx, status_val)
        
        # --- TASK B: APPEND TO TRIAL TIMELINE (Full History) ---
        timeline_sheet = client.open_by_key(TRIAL_TIMELINE_ID).get_worksheet(0)
        
        # Ensure the list of values follows the EXACT order of your headers
        row_to_append = list(full_data_dict.values())
        timeline_sheet.append_row(row_to_append)

        return True, "Both Cloud Databases updated successfully."

    except Exception as e:
        return False, f"Cloud Sync Error: {str(e)}"
3. Update the "Submit" Button Logic
In the if submit_trial: block at the bottom of your script, call this new function instead of the old one:

Python
if submit_trial:
    with st.status("Syncing to Cloud...", expanded=True) as status:
        # ... (your existing local parquet saving code) ...
        
        # Call the new dual-update function
        success, msg = update_cloud_databases(search_input, current_trial_ref, full_data)
        
        if success:
            st.session_state.submitted = True
            st.rerun()
        else:
            st.error(msg)
Why this fixes the "10000" error:
Direct IDs: By separating MASTER_TRACKER_ID and TRIAL_TIMELINE_ID, the code no longer tries to find "10000" in the wrong sheet.

Append vs Update: The Master Tracker is updated (overwriting the old status), but the Timeline is appended (adding a new row at the bottom), so you keep a history of every single trial ever done.

Important: Make sure you have shared both Google Sheets with the service account email found in your secrets TOML.

must i replace this complete code: def update_tracker_status(pre_prod_no, current_trial_ref, manual_date=None):

    import gspread

    from google.oauth2.service_account import Credentials



    trial_suffix = current_trial_ref.split('_')[-1] if '_' in current_trial_ref else current_trial_ref



    if manual_date:

        try:

            date_obj = datetime.strptime(manual_date, "%Y-%m-%d")

            date_str = date_obj.strftime('%d/%m/%Y')

        except:

            date_str = manual_date

        combined_value = f"{trial_suffix} - {date_str}"

    else:

        combined_value = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"



    try:

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:

             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

       

        creds = Credentials.from_service_account_info(creds_info, scopes=scope)

        client = gspread.authorize(creds)

        tracker_spreadsheet = client.open_by_key(TRACKER_FILE_ID)

        tracker_worksheet = tracker_spreadsheet.get_worksheet(0)



        def pad_id(input_val):

            if pd.isna(input_val) or str(input_val).strip() == '':

                return ""

            return str(input_val).strip().split('.')[0]



        search_id = pad_id(pre_prod_no)

        import re

        # Creates a regex that matches the ID exactly

        search_re = re.compile(rf"^{search_id}$")

        cell = tracker_worksheet.find(search_re, in_column=1) e with this code: def update_cloud_databases(pre_prod_no, current_trial_ref, full_data_dict):

    """Handles all Google Sheets updates in one go."""

    import gspread

    from google.oauth2.service_account import Credentials



    # --- 1. SETUP AUTH ---

    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]

    if isinstance(creds_info, dict) and "private_key" in creds_info:

         creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

    

    creds = Credentials.from_service_account_info(creds_info, scopes=scope)

    client = gspread.authorize(creds)



    try:

        # --- TASK A: UPDATE MASTER PROJECT TRACKER (Status Only) ---

        master_sheet = client.open_by_key(MASTER_TRACKER_ID).get_worksheet(0)

        

        # Clean the ID for searching

        search_id = str(pre_prod_no).strip().split('.')[0]

        cell = master_sheet.find(search_id, in_column=1)

        

        if cell:

            headers = [h.strip() for h in master_sheet.row_values(1)]

            col_name = "Injection trial requested"

            if col_name in headers:

                col_idx = headers.index(col_name) + 1

                # Format: T1 - 23/04/2026

                trial_suffix = current_trial_ref.split('_')[-1]

                status_val = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"

                master_sheet.update_cell(cell.row, col_idx, status_val)

        

        # --- TASK B: APPEND TO TRIAL TIMELINE (Full History) ---

        timeline_sheet = client.open_by_key(TRIAL_TIMELINE_ID).get_worksheet(0)

        

        # Ensure the list of values follows the EXACT order of your headers

        row_to_append = list(full_data_dict.values())

        timeline_sheet.append_row(row_to_append)



        return True, "Both Cloud Databases updated successfully."



    except Exception as e:

        return False, f"Cloud Sync Error: {str(e)}"

Yes, you should replace the old function with the new one.

The new function (update_cloud_databases) is superior because it handles two different spreadsheets at once. The old function only knew how to talk to one sheet, which is why it couldn't find the "10000" ID—it was likely looking in the "Timeline" sheet instead of the "Project Tracker" sheet.

Here is exactly how to handle the replacement and the other small changes needed to make it work:

1. The Replacement
Delete the entire def update_tracker_status(...) block (including the try/except inside it) and paste the def update_cloud_databases(...) block in its place.

2. Update your Configuration (Top of file)
Make sure you have these two IDs defined at the top of your code so the new function knows where to go:

Python
# Use your actual Spreadsheet IDs here
MASTER_TRACKER_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M" 
TRIAL_TIMELINE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"
3. Fix the "Sync" Button (Middle of file)
In your code, you have a button labeled 🔄 Sync Master Tracker. Since we changed the function name, you need to update that call (around line 250):

Change this:

Python
success, msg = sync_last_trial_to_cloud(search_input) # This function calls the old name
To this:
Update the sync_last_trial_to_cloud function to use the new logic, or simply update the button to call the new function directly if you have the data ready.

4. Update the "Submit" Logic (Bottom of file)
Around line 335, where you actually save the form, you need to change the function call to match the new name and pass the full_data dictionary.

Change this:

Python
# OLD CALL
success, msg = update_tracker_status(search_input, current_trial_ref)
To this:

Python
# NEW CALL
success, msg = update_cloud_databases(search_input, current_trial_ref, full_data)
Why this is a better way:
Atomicity: When you hit "Submit," it now ensures both the Master Tracker (status update) and the Trial Timeline (full data log) are updated before it tells you "Success."

No Column Confusion: It uses the MASTER_TRACKER_ID specifically to search for the Pre-Prod No., and TRIAL_TIMELINE_ID specifically to add the new history row.

Data Integrity: By passing full_data_dict, you are making sure the exact same data saved to your local .parquet file is what ends up in the Google Sheet.



Error deleting entry: 'Trial Ref' when I try to delete the trial in Injection Trial Data Entry streamlit file

This error is happening because the delete_trial_entry function is still looking for a column named 'Trial Ref', but based on your recent changes, that column has been renamed to 'Trial Reference' in your Parquet file.

When you try to filter the data to delete a row, Pandas can't find that column name and crashes.

The Fix
You need to update the delete_trial_entry function (around line 62 in your original code) to use the correct column name.

Replace your current function with this one:

Python
def delete_trial_entry(trial_ref):
    """Removes a specific trial reference from the submissions file."""
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            df = pd.read_parquet(SUBMISSIONS_FILE)
            
            # CHANGE 'Trial Ref' TO 'Trial Reference'
            if 'Trial Reference' in df.columns:
                df_filtered = df[df['Trial Reference'] != trial_ref]
                df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)
                return True
            else:
                st.error("Column 'Trial Reference' not found in database.")
                return False
                
        except Exception as e:
            st.error(f"Error deleting entry: {e}")
            return False
    return False
Why this is happening
In your code, there was a mismatch between how you saved the data and how you deleted it:

Saving: You used full_data = {"Trial Reference": ...}

Deleting: You were using df['Trial Ref']

Because the names didn't match exactly, Pandas threw a KeyError.

One last check
Make sure that in your display_trial_history function, the button also passes the correct reference:

Python
# Ensure this line uses 'Trial Reference' as well
if st.button(f"Delete", key=f"del_{row['Trial Reference']}_{index}"):
    if delete_trial_entry(row['Trial Reference']):
        # ... rest of code
Once these two spots are updated to use 'Trial Reference', your delete button will work perfectly!

The delete button works ie, I deleted T5, T4, T3 and T2 but the google spreadsheet retains T5 and the Project Tracker retains T5 and the date in the 'Injection trial requested' textbox. It should show T1 and the date and the Trial Timeline google sheet should show T1 as the trial reference

The reason the Google Sheets (both the Project Tracker and the Trial Timeline) aren't updating when you delete a row is that your delete_trial_entry function only removes the data from your local Parquet file. It doesn't currently have the "permission" or the code to reach out to Google and delete rows or update statuses there.

To fix this, we need to trigger a "Resync" after a deletion so the Google Sheets reflect the new "latest" trial.

1. Update your delete_trial_entry function
Update this function to return the Pre-Prod No. of the deleted item so we know which project needs a cloud refresh.

Python
def delete_trial_entry(trial_ref):
    """Removes a trial from local parquet and returns the Pre-Prod No. to trigger a sync."""
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            df = pd.read_parquet(SUBMISSIONS_FILE)
            # Find the Pre-Prod No. before we delete the row
            target_row = df[df['Trial Reference'] == trial_ref]
            if target_row.empty:
                return False, None
            
            pre_prod_no = target_row.iloc[0]['Pre-Prod No.']
            
            # Perform deletion
            df_filtered = df[df['Trial Reference'] != trial_ref]
            df_filtered.to_parquet(SUBMISSIONS_FILE, index=False)
            
            return True, pre_prod_no
        except Exception as e:
            st.error(f"Error deleting entry: {e}")
            return False, None
    return False, None
2. Update the Delete Button Logic
Now, update the code inside display_trial_history (around line 85) to call the Cloud Sync immediately after the local deletion.

Python
# Inside display_trial_history, under the Delete button:
if st.button(f"Delete", key=f"del_{row['Trial Reference']}_{index}"):
    success, p_no = delete_trial_entry(row['Trial Reference'])
    if success:
        st.success(f"Deleted {row['Trial Reference']} locally...")
        
        # TRIGGER CLOUD SYNC
        # This will look at the remaining local trials and push the new 'latest' one to Google
        sync_success, msg = sync_last_trial_to_cloud(p_no)
        
        if sync_success:
            st.success("Cloud updated to reflect previous trial!")
        else:
            st.warning(f"Local delete worked, but Cloud Sync failed: {msg}")
            
        time.sleep(1) 
        st.rerun()
                st.divider()
        else:
            st.write("No previous trial history found.")

def update_cloud_databases(pre_prod_no, current_trial_ref, full_data_dict):
    """Handles all Google Sheets updates in one go."""
    import gspread
    from google.oauth2.service_account import Credentials

    # --- 1. SETUP AUTH ---
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else st.secrets["connections"]["gsheets"]
    if isinstance(creds_info, dict) and "private_key" in creds_info:
         creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)

    try:
        # --- TASK A: UPDATE MASTER PROJECT TRACKER (Status Only) ---
        master_sheet = client.open_by_key(MASTER_TRACKER_ID).get_worksheet(0)
        
        # Clean the ID for searching
        search_id = str(pre_prod_no).strip().split('.')[0]
        cell = master_sheet.find(search_id, in_column=1)
        
        if cell:
            headers = [h.strip() for h in master_sheet.row_values(1)]
            col_name = "Injection trial requested"
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                # Format: T1 - 23/04/2026
                trial_suffix = current_trial_ref.split('_')[-1]
                status_val = f"{trial_suffix} - {datetime.now().strftime('%d/%m/%Y')}"
                master_sheet.update_cell(cell.row, col_idx, status_val)
        
        # --- TASK B: APPEND TO TRIAL TIMELINE (Full History) ---
        timeline_sheet = client.open_by_key(TRIAL_TIMELINE_ID).get_worksheet(0)
        
        # Ensure the list of values follows the EXACT order of your headers
        row_to_append = list(full_data_dict.values())
        timeline_sheet.append_row(row_to_append)

        return True, "Both Cloud Databases updated successfully."

    except Exception as e:
        return False, f"Cloud Sync Error: {str(e)}"

def sync_last_trial_to_cloud(pre_prod_no):
    if not os.path.exists(SUBMISSIONS_FILE):
        return False, "No history file found."
    try:
        df_history = pd.read_parquet(SUBMISSIONS_FILE)
        
        # 1. Clean data: Ensure Pre-Prod No. is a string and drop rows where Trial Ref is missing
        df_history['Pre-Prod No.'] = df_history['Pre-Prod No.'].astype(str)
        df_history = df_history.dropna(subset=['Trial Ref'])
        
        project_history = df_history[df_history['Pre-Prod No.'] == str(pre_prod_no)].copy()
        
        if project_history.empty:
            return update_tracker_status(pre_prod_no, "None", manual_date="No Trials") 

        # 2. Extract number safely: fill NaN with 0 before converting to int
        project_history['Trial_Num'] = (
            project_history['Trial Ref']
            .str.extract(r'(\d+)$')
            .fillna(0) # If no number found, use 0
            .astype(int)
        )
        
        # 3. Get the latest entry
        latest_trial = project_history.sort_values(by=['Trial_Num'], ascending=False).iloc[0]
        
        return update_tracker_status(pre_prod_no, latest_trial['Trial Ref'], manual_date=latest_trial['Date'])
    except Exception as e:
        return False, f"Sync Logic Error: {str(e)}"

def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, txt="Injection Trial Report", ln=True, align='C')
    pdf.set_draw_color(50, 50, 50)
    pdf.line(10, 22, 200, 22)
    pdf.ln(10)

    def add_section(title):
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 8, txt=f" {title}", ln=True, fill=True)
        pdf.ln(2)

    def add_row(label, value, label2="", value2=""):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(45, 7, txt=f"{label}:", border=0)
        pdf.set_font("Arial", size=10)
        pdf.cell(50, 7, txt=f"{str(value)}", border=0)
        
        if label2:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(45, 7, txt=f"{label2}:", border=0)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 7, txt=f"{str(value2)}", border=0)
        pdf.ln(7)

    # Section 1: Admin
    add_section("1. Sales & Administration")
    add_row("Trial Ref", data.get("Trial Reference"), "Date", data.get("Date"))
    add_row("Pre-Prod No.", data.get("Pre-Prod No."), "Sales Rep", data.get("Sales Rep"))
    add_row("Client", data.get("Client"), "Target To", data.get("Target to"))
    add_row("Operator", data.get("Operator"), "Trial Qty", data.get("Trial Quantity"))
    add_row("Prod Machine", data.get("Production Machine"), "Trial Machine", data.get("Trial Machine"))
    pdf.ln(5)

    # Section 2: Product Specs
    add_section("2. Product Specifications")
    
    # --- DESCRIPTION (Special wrap-around handling) ---
    pdf.set_font("Arial", "B", 10)
    pdf.cell(45, 7, txt="Description:", border=0)
    pdf.set_font("Arial", size=10)
    # Using multi_cell for wrap-around. 0 means extend to right margin.
    pdf.multi_cell(0, 7, txt=str(data.get("Description", ""))) 
    
    # Continue with other rows
    add_row("Product Code", data.get("Product Code"), "Material", data.get("Material"))
    add_row("Supplier", data.get("Supplier"), "Cap/Lid Style", data.get("Cap_Lid Style"))
    add_row("Cap/Lid Material", data.get("Cap_Lid Material"), "Diameter", data.get("Diameter"))
    add_row("Length", data.get("Length"), "Orifice", data.get("Orifice"))
    add_row("Mix %", data.get("Mix_%"), "Pigment Grade", data.get("Pigment_MB Grade"))
    add_row("Pre-mix %", data.get("Pre-mix %"), "Tinuvin", data.get("Tinuvin"))
    add_row("Dosing Fitted", data.get("Dosing Unit Fitted"), "Dosing Calib", data.get("Dosing Calibrated"))
    pdf.ln(5)

    # Section 3 & 4: Settings
    add_section("3. Dosing & 4. Process Settings")
    add_row("Colour Set", data.get("Colour Set"), "Colour Actual", data.get("Colour Actual"))
    add_row("Shot Weight", data.get("Shot Weight"), "Dosing Time", data.get("Dosing Time"))
    add_row("Inj Pressure", data.get("Inj Pressure"), "Hold Pressure", data.get("Holding Pressure"))
    add_row("Inj Speed", data.get("Injection Speed"), "Back Pressure", data.get("Back Pressure"))
    add_row("Cycle Time", data.get("Cycle Time"), "Cooling Time", data.get("Cooling Time"))
    pdf.ln(5)

    # Section 5: Observations
    add_section("5. Trial Observations")
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 7, txt=str(data.get("Observations", "")))

    return pdf.output(dest='S').encode('latin-1')

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- SETTINGS ---
TRACKER_FILE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"

# --- GOOGLE SHEETS INITIALIZATION TOOL ---

def initialize_google_sheet_headers():
    """Creates headers in the 'Trial Timeline' spreadsheet if it is empty."""
    
    # These headers are extracted exactly from your 'full_data' dictionary keys
    headers = [
        "Trial Reference", "Pre-Prod No.", "Date", "Sales Rep", "Target to",
        "Client", "Trial Quantity", "Operator", "Production Machine",
        "Trial Machine", "Description", "Length", "Orifice", "Supplier",
        "Cap_Lid Style", "Cap_Lid Material", "Diameter", "Mix_%",
        "Product Code", "Material", "Pigment_MB Grade", "Pre-mix %",
        "Tinuvin", "Dosing Unit Fitted", "Dosing Calibrated", "Colour Set",
        "Colour Actual", "Colour Percentage", "Shot Weight", "Dosing Time",
        "Inj Pressure", "Holding Pressure", "Injection Speed", "Back Pressure",
        "Cycle Time", "Cooling Time", "Dosage Stroke", "Decompression",
        "Observations"
    ]

    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Using the specific secrets key for your Trial Timeline credentials
        # Replace 'trial_timeline_db' with whatever name you gave your new TOML section
        if "trial_timeline_db" in st.secrets:
            creds_info = st.secrets["trial_timeline_db"]
        elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_info = st.secrets["connections"]["gsheets"]
        else:
            creds_info = st.secrets["gcp_service_account"]

        if isinstance(creds_info, dict) and "private_key" in creds_info:
             creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Opening the new Trial Timeline Spreadsheet ID
        spreadsheet = client.open_by_key(TRACKER_FILE_ID)
        worksheet = spreadsheet.get_worksheet(0) 

        # Check for existing data
        if not worksheet.acell('A1').value:
            worksheet.insert_row(headers, 1)
            # Optional: Freeze the top row so it stays visible when scrolling
            worksheet.freeze(rows=1)
            st.success("✅ 'Trial Timeline' headers created successfully!")
        else:
            st.warning("⚠️ Sheet already contains data. Headers were not overwritten.")

    except Exception as e:
        st.error(f"Failed to initialize Trial Timeline headers: {e}")

# Trigger button for the sidebar
if st.sidebar.button("🛠️ Setup Trial Timeline Headers"):
    initialize_google_sheet_headers()

# --- INITIALIZE SESSION STATE ---
if 'lookup_data' not in st.session_state:
    st.session_state.lookup_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- SIDEBAR LOGIC ---
if st.sidebar.button("♻️ Refresh Data Sources"):
    st.cache_data.clear()
    st.success("Cache cleared!")

# --- HEADER & SEARCH ---
st.title("Injection Trial Data Entry")
st.subheader("Search Project Tracker")

col_s1, col_s2 = st.columns([1, 3])
with col_s1:
    search_input = st.text_input("Enter Pre-Prod No. (e.g. 11925):")
with col_s2:
    st.write("##") 
    if st.button("Pull Information"):
        if search_input:
            data = get_project_data(search_input)
            if data:
                st.session_state.lookup_data = data
                st.success(f"Project details loaded for {search_input}")
            else:
                st.warning("No project data found.")
                st.session_state.lookup_data = {}

st.divider()

# --- MAIN LOGIC (Only runs if search_input is provided) ---
if search_input:
    # 1. Trial History & Sync
    st.subheader(f"Trial Timeline: {search_input}")
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.caption("If you deleted entries, use the Sync button to update the Master Tracker.")
    with col_h2:
        if st.button("🔄 Sync Master Tracker"):
            success, msg = sync_last_trial_to_cloud(search_input)
            if success:
                st.success("Master Tracker updated!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Sync failed: {msg}")

    display_trial_history(search_input)
    st.divider()

    # 2. Success & PDF Download Section
    if st.session_state.get('submitted', False):
        st.success("🎉 Entry Saved Successfully!")
        if 'last_submission_data' in st.session_state:
            try:
                pdf_bytes = create_pdf(st.session_state.last_submission_data)
                st.download_button(
                    label="📥 Download Trial Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"Trial_{st.session_state.last_submission_data['Trial Reference']}.pdf",
                    mime="application/pdf",
                    key="download_pdf_main"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
        
        if st.button("Start Next Entry"):
            st.session_state.submitted = False 
            if 'last_submission_data' in st.session_state:
                del st.session_state.last_submission_data
            st.rerun()
        st.divider()

    # 3. New Trial Entry Form
    ld = st.session_state.get('lookup_data', {})
    current_trial_ref = get_next_trial_reference(search_input)

    with st.form("injection_xlsm_form", clear_on_submit=True):
        st.subheader(f"New Trial Entry: {current_trial_ref}")
        
        # Form Sections
        st.subheader("1. Sales & Administration")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            trial_date = st.date_input("Date", datetime.now())
            sales_rep = st.text_input("Sales Rep", value=ld.get('Sales Rep', ''))
        with s2:
            st.text_input("Base Pre-Prod No.", value=search_input, disabled=True)
            active_ref = st.text_input("Trial Reference", value=current_trial_ref, disabled=True)
            target_to = st.text_input("Target to", value=ld.get('Target to', ''))
        with s3:
            client = st.text_input("Client", value=ld.get('Client', ''))
            trial_qty = st.number_input("Trial Quantity", step=1)
        with s4:
            operator = st.text_input("Operator")
            machine_prod = st.text_input("Production Machine", value=ld.get('Machine', ''))
            machine_trial = st.text_input("Trial Machine", value=ld.get('Trial Machine', ''))

        st.divider()
        st.subheader("2. Product Specifications")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            description = st.text_input("Description", value=ld.get('Project Description', ''))
            length = st.text_input("Length", value=str(ld.get('Length', '')))
            orifice = st.text_input("Orifice", value=str(ld.get('Orifice', '')))
            supplier = st.text_input("Supplier", value=str(ld.get('Supplier', '')))
        with p2:
            cap_lid_style = st.text_input("Cap_Lid Style", value=ld.get('Cap_Lid Style', ''))
            cap_lid_material = st.text_input("Cap_Lid Material", value=ld.get('Cap_Lid Material', ''))
            cap_lid_diameter = st.text_input("Cap_Lid Diameter", value=str(ld.get('Diameter', '')))
            mix = st.text_input("Mix_%", value=str(ld.get('Mix_%', '')))
        with p3:
            product_code = st.text_input("Product Code", value=ld.get('Product Code', ''))
            material = st.text_input("Material", value=ld.get('Material', ''))
            pigment = st.text_input("Pigment_MB Grade", value=ld.get('Pigment_MB Grade', ''))
            pre_mix_perc = st.text_input("Pre-mix %", value=str(ld.get('if no_dosing unit, what percentage was material pre-mixed', '')))
        with p4:
            tinuvin_val = st.radio("Tinuvin", options=["Yes", "No"], horizontal=True)
            dosing_fitted = st.radio("Is dosing unit fitted", options=["Yes", "No"], horizontal=True)
            dosing_calib = st.radio("Is dosing unit calibrated", options=["Yes", "No"], horizontal=True)

        st.divider()
        st.subheader("3. Dosing Unit Settings")
        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: colour_set = st.text_input("Colour Set Value", value=ld.get('Colour Set Value', ''))
        with d2: colour_act = st.text_input("Colour Actual", value=ld.get('Colour Actual', ''))
        with d3: colour_perc = st.text_input("Colour Percentage", value=ld.get('Colour Percentage', ''))
        with d4: shot_w = st.text_input("Shot Weight", value=ld.get('Shot Weight', ''))
        with d5: dosing_time = st.text_input("Dosing Time", value=ld.get('Dosing Time', ''))

        st.divider()
        st.subheader("4. Machine Process Settings")
        pr1, pr2, pr3, pr4 = st.columns(4)
        with pr1:
            inj_p = st.number_input("Injection Pressure (bar)", step=1)
            hold_p = st.number_input("Holding Pressure (bar)", step=1)
        with pr2:
            inj_s = st.number_input("Injection Speed (mm/s)", step=1)
            back_p = st.number_input("Back Pressure (bar)", step=1)
        with pr3:
            cyc_t = st.number_input("Total Cycle Time (s)", format="%.2f")
            cool_t = st.number_input("Cooling Time (s)", format="%.2f")
        with pr4:
            dos_s = st.number_input("Dosage Stroke (mm)", step=1)
            dec_m = st.number_input("Decompression (mm)", step=1)

        st.divider()
        st.subheader("5. Trial Observations")
        notes = st.text_area("Observations")

        submit_trial = st.form_submit_button("Submit Trial Entry")

    if submit_trial:
            with st.status("Saving Data...", expanded=True) as status:
                # Create the full dictionary for the PDF and Parquet
                full_data = {
                    "Trial Reference": current_trial_ref,
                    "Pre-Prod No.": str(search_input), # Force string
                    "Date": trial_date.strftime("%Y-%m-%d"),
                    "Sales Rep": str(sales_rep),
                    "Target to": str(target_to),
                    "Client": str(client),
                    "Trial Quantity": str(trial_qty),
                    "Operator": str(operator),
                    "Production Machine": str(machine_prod),
                    "Trial Machine": str(machine_trial),
                    "Description": str(description),
                    "Length": str(length),
                    "Orifice": str(orifice),
                    "Supplier": str(supplier),
                    "Cap_Lid Style": str(cap_lid_style),
                    "Cap_Lid Material": str(cap_lid_material),
                    "Diameter": str(cap_lid_diameter),
                    "Mix_%": str(mix),
                    "Product Code": str(product_code),
                    "Material": str(material),
                    "Pigment_MB Grade": str(pigment),
                    "Pre-mix %": str(pre_mix_perc),
                    "Tinuvin": str(tinuvin_val),
                    "Dosing Unit Fitted": str(dosing_fitted),
                    "Dosing Calibrated": str(dosing_calib),
                    "Colour Set": str(colour_set),
                    "Colour Actual": str(colour_act),
                    "Colour Percentage": str(colour_perc),
                    "Shot Weight": str(shot_w),
                    "Dosing Time": str(dosing_time),
                    "Inj Pressure": f"{inj_p} bar",
                    "Holding Pressure": f"{hold_p} bar",
                    "Injection Speed": f"{inj_s} mm/s",
                    "Back Pressure": f"{back_p} bar",
                    "Cycle Time": f"{cyc_t}s",
                    "Cooling Time": f"{cool_t}s",
                    "Dosage Stroke": str(dos_s),
                    "Decompression": str(dec_m),
                    "Observations": str(notes)
                }
                
                st.session_state.last_submission_data = full_data

                # Parquet Save Logic with Type Safety
                df_new = pd.DataFrame([full_data])
                
                if os.path.exists(SUBMISSIONS_FILE):
                    try:
                        df_existing = pd.read_parquet(SUBMISSIONS_FILE)
                        # Ensure both dataframes have identical column types (Strings) to prevent Arrow errors
                        df_existing = df_existing.astype(str)
                        df_new = df_new.astype(str)
                        df_final = pd.concat([df_existing, df_new], ignore_index=True)
                    except Exception as e:
                        st.warning(f"Existing file schema mismatch. Starting fresh: {e}")
                        df_final = df_new
                else:
                    df_final = df_new

                # FINAL STEP: Ensure everything is string before writing to Parquet
                df_final = df_final.astype(str)
                df_final.to_parquet(SUBMISSIONS_FILE, index=False, engine='pyarrow')

                # Cloud Sync
                success, msg = update_cloud_databases(search_input, current_trial_ref, full_data)
                if success:
                    st.session_state.submitted = True
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Cloud Sync Failed: {msg}")    


import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import io
import gspread
from google.oauth2.service_account import Credentials

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Injection Trial Data Entry")

# --- CONFIGURATION ---
MASTER_TRACKER_ID = "1b7ksuTX2C7ns89AXc7Npki70KqjcXf1-oxIkZjTuq8M"
TRIAL_TIMELINE_ID = "1UtoZnl8vLKmP47UhxdPDzCZABhccWcyEnC-YV5mTW-Y"

# --- DIRECTORY SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME_PARQUET = os.path.join(BASE_DIR, "ProjectTracker_Combined.parquet")
SUBMISSIONS_FILE = os.path.join(BASE_DIR, "Trial_Submissions.parquet")

# --- HELPERS ---
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["connections"]["gsheets"]
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

def get_project_data(pre_prod_no):
    if not os.path.exists(FILENAME_PARQUET): return None
    df = pd.read_parquet(FILENAME_PARQUET)
    search_id = str(pre_prod_no).strip().split('.')[0]
    df['Pre-Prod No.'] = df['Pre-Prod No.'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    result = df[df['Pre-Prod No.'] == search_id]
    return result.iloc[0].to_dict() if not result.empty else None

def get_next_trial_reference(pre_prod_no):
    if not os.path.exists(SUBMISSIONS_FILE): return f"{pre_prod_no}_T1"
    df = pd.read_parquet(SUBMISSIONS_FILE)
    count = len(df[df['Pre-Prod No.'] == str(pre_prod_no)])
    return f"{pre_prod_no}_T{count + 1}"

def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Injection Trial Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=9)
    for key, value in data.items():
        pdf.set_font("Arial", "B", 9)
        pdf.cell(60, 7, txt=f"{key}:", border=0)
        pdf.set_font("Arial", size=9)
        pdf.cell(0, 7, txt=f"{str(value)}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- MAIN UI ---
st.title("Injection Trial Data Entry")
search_input = st.text_input("Enter Pre-Prod No.:")

if search_input:
    ld = get_project_data(search_input)
    if not ld:
        st.warning("Project not found.")
        st.stop()
    
    current_trial_ref = get_next_trial_reference(search_input)

    if st.session_state.get('submitted', False):
        st.success("Entry Saved!")
        pdf_bytes = create_pdf(st.session_state.last_submission)
        st.download_button("📥 Download Report", pdf_bytes, f"{current_trial_ref}.pdf", "application/pdf")
        if st.button("New Entry"):
            st.session_state.submitted = False
            st.rerun()
        st.divider()

    with st.form("trial_form", clear_on_submit=True):
        st.subheader(f"Form: {current_trial_ref}")
        
        # Section 1: Admin
        col = st.columns(4)
        t_date = col[0].date_input("Date", datetime.now())
        s_rep = col[1].text_input("Sales Rep", value=ld.get('Sales Rep', ''))
        client = col[2].text_input("Client", value=ld.get('Client', ''))
        operator = col[3].text_input("Operator")
        
        col = st.columns(4)
        target_to = col[0].text_input("Target to", value=ld.get('Target to', ''))
        t_qty = col[1].number_input("Trial Quantity", step=1)
        m_prod = col[2].text_input("Production Machine", value=ld.get('Machine', ''))
        m_trial = col[3].text_input("Trial Machine")

        # Section 2: Product Specs
        st.divider()
        col = st.columns(4)
        desc = col[0].text_input("Description", value=ld.get('Project Description', ''))
        p_code = col[1].text_input("Product Code", value=ld.get('Product Code', ''))
        material = col[2].text_input("Material", value=ld.get('Material', ''))
        supplier = col[3].text_input("Supplier", value=ld.get('Supplier', ''))

        col = st.columns(4)
        length = col[0].text_input("Length", value=str(ld.get('Length', '')))
        orifice = col[1].text_input("Orifice", value=str(ld.get('Orifice', '')))
        cap_style = col[2].text_input("Cap Style", value=ld.get('Cap_Lid Style', ''))
        cap_mat = col[3].text_input("Cap Material", value=ld.get('Cap_Lid Material', ''))

        col = st.columns(4)
        diam = col[0].text_input("Diameter", value=str(ld.get('Diameter', '')))
        mix_p = col[1].text_input("Mix %", value=str(ld.get('Mix_%', '')))
        pigment = col[2].text_input("Pigment Grade", value=ld.get('Pigment_MB Grade', ''))
        pre_mix = col[3].text_input("Pre-mix %")

        col = st.columns(3)
        tinuvin = col[0].radio("Tinuvin", ["Yes", "No"], horizontal=True)
        d_fitted = col[1].radio("Dosing Fitted", ["Yes", "No"], horizontal=True)
        d_calib = col[2].radio("Dosing Calibrated", ["Yes", "No"], horizontal=True)

        # Section 3: Dosing & Process
        st.divider()
        col = st.columns(5)
        c_set = col[0].text_input("Colour Set")
        c_act = col[1].text_input("Colour Actual")
        c_perc = col[2].text_input("Colour %")
        shot_w = col[3].text_input("Shot Weight")
        d_time = col[4].text_input("Dosing Time")

        col = st.columns(4)
        inj_p = col[0].number_input("Inj Pressure (bar)", step=1)
        hold_p = col[1].number_input("Hold Pressure (bar)", step=1)
        inj_s = col[2].number_input("Inj Speed (mm/s)", step=1)
        back_p = col[3].number_input("Back Pressure (bar)", step=1)

        col = st.columns(4)
        cyc_t = col[0].number_input("Cycle Time (s)", format="%.2f")
        cool_t = col[1].number_input("Cooling Time (s)", format="%.2f")
        d_stroke = col[2].number_input("Dosage Stroke (mm)", step=1)
        decomp = col[3].number_input("Decompression (mm)", step=1)

        notes = st.text_area("Observations")

        if st.form_submit_button("Submit Trial"):
            full_data = {
                "Trial Reference": current_trial_ref,
                "Pre-Prod No.": search_input,
                "Date": t_date.strftime("%Y-%m-%d"),
                "Sales Rep": s_rep,
                "Target to": target_to,
                "Client": client,
                "Trial Quantity": t_qty,
                "Operator": operator,
                "Production Machine": m_prod,
                "Trial Machine": m_trial,
                "Description": desc,
                "Length": length,
                "Orifice": orifice,
                "Supplier": supplier,
                "Cap_Lid Style": cap_style,
                "Cap_Lid Material": cap_mat,
                "Diameter": diam,
                "Mix_%": mix_p,
                "Product Code": p_code,
                "Material": material,
                "Pigment_MB Grade": pigment,
                "Pre-mix %": pre_mix,
                "Tinuvin": tinuvin,
                "Dosing Unit Fitted": d_fitted,
                "Dosing Calibrated": d_calib,
                "Colour Set": c_set,
                "Colour Actual": c_act,
                "Colour Percentage": c_perc,
                "Shot Weight": shot_w,
                "Dosing Time": d_time,
                "Inj Pressure": f"{inj_p} bar",
                "Holding Pressure": f"{hold_p} bar",
                "Injection Speed": f"{inj_s} mm/s",
                "Back Pressure": f"{back_p} bar",
                "Cycle Time": f"{cyc_t}s",
                "Cooling Time": f"{cool_t}s",
                "Dosage Stroke": d_stroke,
                "Decompression": decomp,
                "Observations": notes
            }

            # Save Logic
            df_new = pd.DataFrame([full_data]).astype(str)
            if os.path.exists(SUBMISSIONS_FILE):
                df_hist = pd.read_parquet(SUBMISSIONS_FILE).astype(str)
                pd.concat([df_hist, df_new], ignore_index=True).to_parquet(SUBMISSIONS_FILE, index=False)
            else:
                df_new.to_parquet(SUBMISSIONS_FILE, index=False)

            # Cloud Sync
            client = get_gspread_client()
            # Update Tracker
            m_sheet = client.open_by_key(MASTER_TRACKER_ID).get_worksheet(0)
            cell = m_sheet.find(search_input, in_column=1)
            if cell:
                headers = [h.strip() for h in m_sheet.row_values(1)]
                col_idx = headers.index("Injection trial requested") + 1
                m_sheet.update_cell(cell.row, col_idx, f"{current_trial_ref.split('_')[-1]} - {datetime.now().strftime('%d/%m/%Y')}")
            
            # Append Timeline
            t_sheet = client.open_by_key(TRIAL_TIMELINE_ID).get_worksheet(0)
            t_sheet.append_row(list(full_data.values()))

            st.session_state.last_submission = full_data
            st.session_state.submitted = True
            st.rerun()
import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Load Recovery Dashboard", layout="wide")

# ====================== CUSTOM STYLING ======================
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1e3a8a !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .main { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

st.title("🚛 Load Recovery Specialist Dashboard")
st.markdown("**Autonomous Trucking — Real-time Load Recovery Tracking**")

def load_data():
    try:
        df = pd.read_csv("incidents.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "Date", "Incident_ID", "Truck_ID", "Trailer_ID", "Load_ID",
            "Alert_Time", "First_Response_Time", "Recovery_Complete_Time",
            "Incident_Type", "Resolution_Method", "Customer_Notified_Time",
            "Status", "Success_YN", "Recovery_Cost_USD", "Downtime_Hours", "Notes"
        ])
    
    # Fix data types
    for col in ["First_Response_Time", "Recovery_Complete_Time", "Customer_Notified_Time", "Alert_Time", "Status", "Success_YN", "Resolution_Method", "Notes"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['nan', 'None', ''], '')
        else:
            df[col] = ''
    
    df["Recovery_Cost_USD"] = pd.to_numeric(df.get("Recovery_Cost_USD", 0), errors='coerce').fillna(0.0)
    df["Downtime_Hours"] = pd.to_numeric(df.get("Downtime_Hours", 0), errors='coerce').fillna(0.0)
    
    if "Status" in df.columns:
        df.loc[df["Status"].isin(['', 'nan', 'None']), "Status"] = "Open"
    
    return df

df = load_data()

page = st.sidebar.selectbox("Navigate", ["📊 Dashboard", "🔴 Open Cases", "➕ Log New Incident", "✏️ Update Incident", "📋 All Incidents"])

# ====================== UPDATE INCIDENT ======================
elif page == "Update Incident":
    st.header("✏️ Update Existing Incident (Close or Edit)")

    if df.empty:
        st.info("No incidents to update yet.")
    else:
        selected_id = st.selectbox("Select Incident to Update", df["Incident_ID"].tolist(), key="update_key")

        if selected_id:
            incident_idx = df[df["Incident_ID"] == selected_id].index[0]
            incident = df.loc[incident_idx]

            st.subheader(f"Updating: {selected_id} - {incident['Truck_ID']} | {incident['Incident_Type']}")

            col1, col2 = st.columns(2)
            first_response = col1.text_input("First Response Time", value=str(incident.get("First_Response_Time", "")))
            recovery_complete = col2.text_input("Recovery Complete Time", value=str(incident.get("Recovery_Complete_Time", "")))

            resolution = st.selectbox("Resolution Method", 
                ["", "Remote reset", "Tow + tractor swap", "Remote + partner swap", "Reroute", "Transload"])

            customer_notified = st.text_input("Customer Notified Time", value=str(incident.get("Customer_Notified_Time", "")))
            cost = st.number_input("Final Recovery Cost ($)", value=float(incident.get("Recovery_Cost_USD", 0)))
            success = st.selectbox("Final Success?", ["", "Y", "N"])
            status = st.selectbox("Status", ["Open", "In Progress", "Closed"])

            notes = st.text_area("Updated Notes", value=str(incident.get("Notes", "")))

            if st.button("✅ Update & Save Incident", type="primary", use_container_width=True):
                df.at[incident_idx, "First_Response_Time"] = first_response
                df.at[incident_idx, "Recovery_Complete_Time"] = recovery_complete
                df.at[incident_idx, "Resolution_Method"] = resolution
                df.at[incident_idx, "Customer_Notified_Time"] = customer_notified
                df.at[incident_idx, "Recovery_Cost_USD"] = cost
                df.at[incident_idx, "Success_YN"] = success
                df.at[incident_idx, "Status"] = status
                df.at[incident_idx, "Notes"] = notes

                # Auto-calculate MTTR
                if recovery_complete and incident.get("Alert_Time"):
                    try:
                        alert_dt = pd.to_datetime(incident["Alert_Time"])
                        complete_dt = pd.to_datetime(recovery_complete)
                        df.at[incident_idx, "Downtime_Hours"] = round((complete_dt - alert_dt).total_seconds() / 3600, 2)
                    except:
                        pass

                df.to_csv("incidents.csv", index=False)
                st.success(f"✅ Incident **{selected_id}** updated successfully!")
                st.balloons()
                time.sleep(1.5)
                st.rerun()

# (The rest of your code - Dashboard, Open Cases, Log New Incident, All Incidents - remains the same)

st.sidebar.caption("Volvo Trucks | Load Recovery Specialist Tool")
import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Load Recovery Dashboard", layout="wide")

# ====================== STYLING ======================
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

# Clean navigation (no emojis to avoid bugs)
page = st.sidebar.selectbox("Navigate", [
    "Dashboard", 
    "Open Cases", 
    "Log New Incident", 
    "Update Incident", 
    "All Incidents"
])

# ====================== DASHBOARD ======================
if page == "Dashboard":
    st.header("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    total = len(df)
    open_cases = len(df[df["Status"].isin(["Open", "In Progress"])])
    success_rate = (df["Success_YN"].eq("Y").sum() / len(df[df["Success_YN"].isin(["Y","N"])]) * 100) if len(df[df["Success_YN"].isin(["Y","N"])]) > 0 else 0
    avg_mttr = df["Downtime_Hours"].mean() if total > 0 else 0

    col1.metric("Total Incidents", total)
    col2.metric("Open Cases", open_cases)
    col3.metric("Success Rate", f"{success_rate:.1f}%")
    col4.metric("Avg MTTR (hrs)", f"{avg_mttr:.2f}")

# ====================== OPEN CASES (with color coding) ======================
elif page == "Open Cases":
    st.header("🔴 Open Cases (Work in Progress)")

    open_df = df[df["Status"].isin(["Open", "In Progress"])].copy()
    
    if open_df.empty:
        st.success("🎉 No open cases right now!")
    else:
        open_df = open_df.copy()
        try:
            open_df["Time_Open_Hours"] = round(
                (pd.to_datetime(datetime.now()) - pd.to_datetime(open_df["Alert_Time"])).dt.total_seconds() / 3600, 1)
        except:
            open_df["Time_Open_Hours"] = 0.0

        filter_option = st.radio("Filter", ["All Open Cases", "High Priority (>8 hrs)"], horizontal=True)

        if filter_option == "High Priority (>8 hrs)":
            open_df = open_df[open_df["Time_Open_Hours"] > 8]

        def color_rows(row):
            hours = row["Time_Open_Hours"]
            if hours > 8:
                return ['background-color: #fee2e2'] * len(row)   # Red
            elif hours > 4:
                return ['background-color: #fef3c7'] * len(row)   # Yellow
            else:
                return ['background-color: #d1fae5'] * len(row)   # Green

        styled_df = open_df.style.apply(color_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.caption("🟢 0–4 hrs | 🟡 4–8 hrs | 🔴 >8 hrs (High Priority)")

# ====================== LOG NEW INCIDENT ======================
elif page == "Log New Incident":
    st.header("➕ Create New Incident")
    col1, col2 = st.columns(2)
    truck_id = col1.text_input("Truck ID *", placeholder="T-007")
    trailer_id = col2.text_input("Trailer ID *", placeholder="1234")
    load_id = st.text_input("Load ID *", placeholder="LD-8923")
    alert_time = st.text_input("Alert Time", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    incident_type = st.selectbox("Incident Type *", ["Sensor fault", "Mechanical brake", "Charging issue", "Weather-related", "Tire issue", "Other"])
    notes = st.text_area("Initial Notes")

    if st.button("Create Incident (Open)", type="primary", use_container_width=True):
        if not truck_id or not trailer_id or not load_id:
            st.error("Truck ID, Trailer ID, and Load ID are required!")
        else:
            new_row = {
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Incident_ID": f"INC-{len(df)+1:03d}",
                "Truck_ID": truck_id,
                "Trailer_ID": trailer_id,
                "Load_ID": load_id,
                "Alert_Time": alert_time,
                "First_Response_Time": "",
                "Recovery_Complete_Time": "",
                "Incident_Type": incident_type,
                "Resolution_Method": "",
                "Customer_Notified_Time": "",
                "Status": "Open",
                "Success_YN": "",
                "Recovery_Cost_USD": 0.0,
                "Downtime_Hours": 0.0,
                "Notes": notes
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv("incidents.csv", index=False)
            st.success(f"Incident {new_row['Incident_ID']} created successfully!")
            st.balloons()
            time.sleep(1.5)
            st.rerun()

# ====================== UPDATE INCIDENT ======================
elif page == "Update Incident":
    st.header("✏️ Update Existing Incident")

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

            resolution = st.selectbox("Resolution Method", ["", "Remote reset", "Tow + tractor swap", "Remote + partner swap", "Reroute", "Transload"])
            customer_notified = st.text_input("Customer Notified Time", value=str(incident.get("Customer_Notified_Time", "")))
            cost = st.number_input("Final Recovery Cost ($)", value=float(incident.get("Recovery_Cost_USD", 0)))
            success = st.selectbox("Final Success?", ["", "Y", "N"])
            status = st.selectbox("Status", ["Open", "In Progress", "Closed"])

            notes = st.text_area("Updated Notes", value=str(incident.get("Notes", "")))

            if st.button("Update & Save Incident", type="primary", use_container_width=True):
                df.at[incident_idx, "First_Response_Time"] = first_response
                df.at[incident_idx, "Recovery_Complete_Time"] = recovery_complete
                df.at[incident_idx, "Resolution_Method"] = resolution
                df.at[incident_idx, "Customer_Notified_Time"] = customer_notified
                df.at[incident_idx, "Recovery_Cost_USD"] = cost
                df.at[incident_idx, "Success_YN"] = success
                df.at[incident_idx, "Status"] = status
                df.at[incident_idx, "Notes"] = notes

                df.to_csv("incidents.csv", index=False)
                st.success(f"Incident {selected_id} updated successfully!")
                st.balloons()
                time.sleep(1.5)
                st.rerun()

# ====================== ALL INCIDENTS ======================
elif page == "All Incidents":
    st.header("All Logged Incidents")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download as CSV", df.to_csv(index=False), "incidents.csv")
    else:
        st.info("No incidents logged yet.")

st.sidebar.caption("Volvo Trucks | Load Recovery Specialist Tool")
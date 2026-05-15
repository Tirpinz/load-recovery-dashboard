import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Load Recovery Dashboard", layout="wide")

# ====================== CUSTOM STYLING ======================
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1e3a8a !important; }
    [data-testid="stSidebar"] * { color: black !important; }
    .main { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

st.title("🚛 Load Recovery Specialist Dashboard")
st.markdown("### Autonomous Trucking - Real-time Load Recovery Tracking")

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

# ====================== DASHBOARD ======================
if page == "📊 Dashboard":
    st.header("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    total = len(df)
    open_cases = len(df[df["Status"].isin(["Open", "In Progress"])])
    high_priority = len(df[(df["Status"].isin(["Open", "In Progress"])) & 
                          (pd.to_datetime(datetime.now()) - pd.to_datetime(df["Alert_Time"])).dt.total_seconds() / 3600 > 8])
    
    success_rate = (df["Success_YN"].eq("Y").sum() / len(df[df["Success_YN"].isin(["Y","N"])]) * 100) if len(df[df["Success_YN"].isin(["Y","N"])]) > 0 else 0
    avg_mttr = df["Downtime_Hours"].mean() if total > 0 else 0

    col1.metric("Total Incidents", total)
    col2.metric("Open Cases", open_cases)
    col3.metric("Success Rate", f"{success_rate:.1f}%")
    col4.metric("Avg MTTR (hrs)", f"{avg_mttr:.2f}")

    # Aging Alerts
    if high_priority > 0:
        st.error(f"🚨 **HIGH PRIORITY**: {high_priority} case(s) open for more than 8 hours!")
    elif open_cases > 0:
        st.warning(f"⚠️ {open_cases} open cases need attention.")
    else:
        st.success("🎉 All cases are currently closed!")

# ====================== OPEN CASES ======================

elif page == "🔴 Open Cases":
    st.header("🔴 Open Cases (Work in Progress)")

    open_df = df[df["Status"].isin(["Open", "In Progress"])].copy()
    
    if open_df.empty:
        st.success("🎉 No open cases right now!")
    else:
        # Calculate Time Open
        open_df = open_df.copy()
        try:
            open_df["Time_Open_Hours"] = round(
                (pd.to_datetime(datetime.now()) - pd.to_datetime(open_df["Alert_Time"])).dt.total_seconds() / 3600, 
                1
            )
        except:
            open_df["Time_Open_Hours"] = 0.0

        # Filter Buttons
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_option = st.radio("Filter", ["All Open Cases", "High Priority (>8 hrs)"], horizontal=True)
        with col2:
            st.write("")

        if filter_option == "High Priority (>8 hrs)":
            open_df = open_df[open_df["Time_Open_Hours"] > 8]

        # Color Coding
        def color_rows(row):
            hours = row["Time_Open_Hours"]
            if hours > 8:
                return ['background-color: #fee2e2'] * len(row)   # Red
            elif hours > 4:
                return ['background-color: #fef3c7'] * len(row)   # Yellow
            else:
                return ['background-color: #d1fae5'] * len(row)   # Green

        st.subheader(f"Showing: **{len(open_df)}** cases")

        styled_df = open_df.style.apply(color_rows, axis=1)

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Time_Open_Hours": st.column_config.NumberColumn("Time Open (hrs)", format="%.1f", help="Sortable")
            }
        )

        st.caption("🟢 0–4 hrs | 🟡 4–8 hrs | 🔴 >8 hrs (High Priority)")
# ====================== LOG NEW INCIDENT ======================
elif page == "➕ Log New Incident":
    st.header("➕ Create New Incident")

    col1, col2 = st.columns(2)
    truck_id = col1.text_input("Truck ID *", placeholder="T-007", key="truck")
    trailer_id = col2.text_input("Trailer ID *", placeholder="1234", key="trailer")
    load_id = st.text_input("Load ID *", placeholder="LD-8923", key="load")
    alert_time = st.text_input("Alert Time", value=datetime.now().strftime("%Y-%m-%d %H:%M"), key="alert")
    incident_type = st.selectbox("Incident Type *", 
        ["Sensor fault", "Mechanical brake", "Charging issue", "Weather-related", "Tire issue", "Other"], key="type")
    notes = st.text_area("Initial Notes", key="notes")

    if st.button("✅ Create Incident (Open)", type="primary", use_container_width=True):
        if not truck_id or not trailer_id or not load_id:
            st.error("❌ Truck ID, Trailer ID, and Load ID are required!")
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
            
            st.success(f"✅ Incident **{new_row['Incident_ID']}** created successfully as **Open**!")
            st.balloons()
            time.sleep(1.8)   # Give time to see the message
            st.rerun()

# ====================== UPDATE INCIDENT ======================
elif page == "✏️ Update Incident":
    st.header("✏️ Update Existing Incident")
    if df.empty:
        st.info("No incidents yet.")
    else:
        selected_id = st.selectbox("Select Incident", df["Incident_ID"].tolist())
        # ... (keep your existing update logic or let me know if you want it updated too)

# ====================== ALL INCIDENTS ======================
elif page == "📋 All Incidents":
    st.header("All Logged Incidents")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download as CSV", df.to_csv(index=False), "incidents.csv")
    else:
        st.info("No incidents logged yet.")

st.sidebar.caption("Autonomous Trucking | Load Recovery Specialist Tool")
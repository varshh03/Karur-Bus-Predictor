import streamlit as st
from datetime import datetime

# --- 1. DATA CONFIGURATION ---
stops = [
    "Old Bus Stand", "Ulavar Sandhai", "Light House", 
    "Thirumanaliyur", "Sungagate", "Terasa Corner", 
    "Terasa Nagar", "GH", "Gandhigramam", 
    "Audha Padhai", "Moolakatanur", "Vadaku Palayam", "College"
]

morning_buses = {"8A": "08:10", "3": "08:15", "1": "08:20", "5B": "08:25", "8": "08:35", "4/2": "08:45"}
afternoon_buses = {"DSM": "16:40", "3_Early": "16:45", "8": "17:00", "3_Mid": "17:10", "SDN": "17:15", "3_Late": "17:30", "5A": "17:35"}

# --- 2. THE SMART LOGIC ENGINE ---
def get_prediction(bus_name, start_idx, end_idx, arr_time, day_type):
    is_morning = end_idx > start_idx 
    
    if day_type == "Sunday":
        return "Very Light", "Sunday holiday: Minimum crowd.", "🟢"
    
    if is_morning:
        if bus_name in ["8", "4/2"] and end_idx == 12: 
            return "Free", "Warning: Reaches college LATE (After 09:00).", "🔴"
        
        if day_type == "Saturday":
            return "Moderate", "Saturday: Reduced school load.", "🟡"

        if bus_name == "1":
            if start_idx <= 1: return "Moderate", "Initial boarding from town.", "🟡"
            elif 2 <= start_idx <= 5: return "Crowded", "School student peak zone.", "🟠"
            else: return "Less Crowded", "School students exited at Terasa/GH.", "🟢"
        
        if start_idx <= 5: return "Crowded", "Peak school/office hours.", "🟠"
        elif 6 <= start_idx <= 7: return "Less Crowded", "Terasa/GH drop-off completed.", "🟢"
        else: return "Free", "Mostly college students only.", "🟢"
    
    else: # Afternoon/Return
        if day_type == "Saturday": return "Moderate", "Saturday return flow.", "🟡"
        if arr_time >= "17:10": return "Less Crowded", "Post-peak: Seats available.", "🟢"
        if start_idx >= 9: return "Highly Crowded", "College exit rush.", "🟠"
        else: return "Moderate", "Normal city flow.", "🟡"

# --- 3. SESSION STATE FOR TIME ---
# This allows the app to start with Live Time but let the user change it
if 'manual_time' not in st.session_state:
    st.session_state.manual_time = datetime.now().time()

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="Karur Transit AI", layout="wide")
st.title("Karur Bus Predictor")

# Sidebar for Inputs
st.sidebar.header("Trip Settings")

# Live Day Detection
now = datetime.now()
live_day = now.strftime("%A")

# Manual Day Selection (Defaults to Current Day)
selected_day = st.sidebar.selectbox("Select Day", 
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 
    index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(live_day))

# TIME INPUT (Linked to Session State)
u_time = st.sidebar.time_input("Set Time (Change to see future buses)", value=st.session_state.manual_time)
st.session_state.manual_time = u_time

# Reset Button
if st.sidebar.button("Reset to Live Time"):
    st.session_state.manual_time = datetime.now().time()
    st.rerun()

# Source and Destination Selection
source_stop = st.sidebar.selectbox("From (Source)", stops)
dest_stop = st.sidebar.selectbox("To (Destination)", stops, index=len(stops)-1)

# --- 5. PROCESSING & DISPLAY ---
if source_stop == dest_stop:
    st.error("Please pick two different stops to see the schedule.")
else:
    start_idx = stops.index(source_stop)
    end_idx = stops.index(dest_stop)
    is_morning = end_idx > start_idx
    u_time_str = u_time.strftime("%H:%M")
    
    # Choose schedule based on direction
    schedule = morning_buses if is_morning else afternoon_buses
    day_status = "Sunday" if selected_day == "Sunday" else ("Saturday" if selected_day == "Saturday" else "Weekday")

    st.subheader(f"Trip: {source_stop} ➡️ {dest_stop}")
    st.markdown(f"**Mode:** {'Towards College' if is_morning else 'Towards Old Bus Stand'} | **Day:** {selected_day} | **Showing from:** {u_time_str}")

    

    # Column Layout for Bus Cards
    cols = st.columns(3)
    found = False
    col_counter = 0

    for bus_id, start_time in schedule.items():
        # Calculate arrival time based on distance from origin (2.5 mins per stop avg)
        origin_offset = start_idx if is_morning else (len(stops) - 1 - start_idx)
        h, m = map(int, start_time.split(':'))
        arr_mins = h * 60 + m + int(origin_offset * 2.5)
        arr_time_str = f"{arr_mins // 60:02d}:{arr_mins % 60:02d}"

        # Show only upcoming buses
        if arr_time_str >= u_time_str:
            found = True
            bus_clean = bus_id.split('_')[0]
            status, reason, icon = get_prediction(bus_clean, start_idx, end_idx, arr_time_str, day_status)
            
            with cols[col_counter % 3]:
                with st.container(border=True):
                    st.write(f"### {icon} Bus {bus_clean}")
                    st.metric("Arrival at your stop", arr_time_str)
                    st.write(f"**Status:** {status}")
                    st.caption(f"Reason: {reason}")
            col_counter += 1

    if not found:
        st.info("No more buses found for the selected criteria. Adjust time to see earlier/later buses.")

# Footer Legend
st.divider()
st.write("**Legend:** 🟢 Light | 🟡 Moderate | 🟠 Crowded | 🔴 Late Arrival Warning")
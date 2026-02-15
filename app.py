import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Discus Scoring App", layout="wide")

# --- QUALIFYING DISTANCES ---
QUALIFYING_STANDARDS = {
    "Girls": 15.0,
    "Junior Boys": 16.0,
    "Intermediate": 22.0, 
    "Senior Boys": 20.0,
    "Senior Girls": 15.0,
    "Intermediate Boys": 22.0
}

# --- STATE MANAGEMENT ---
if 'discus_data' not in st.session_state:
    st.session_state.discus_data = [] 
if 'finalists_generated' not in st.session_state:
    st.session_state.finalists_generated = {} 

# --- HELPER FUNCTIONS ---
def parse_throw(val):
    """Converts string input to float. Returns 0.0 for fouls/empty."""
    if not val or val == "" or val == "-":
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

def get_best_throw(athlete):
    """Returns the single best distance from all 5 throws."""
    throws = [
        athlete.get('t1', ''),
        athlete.get('t2', ''),
        athlete.get('t3', ''),
        athlete.get('t4', ''),
        athlete.get('t5', '')
    ]
    valid_throws = [parse_throw(t) for t in throws]
    return max(valid_throws) if valid_throws else 0.0

# --- SIDEBAR: SETUP ---
with st.sidebar:
    st.header("1. Upload Start List")
    uploaded_file = st.file_uploader("Upload CSV (Category, House, Name)", type=['csv'])
    
    if uploaded_file:
        if st.button("Load Data"):
            try:
                df = pd.read_csv(uploaded_file)
                # Normalize headers
                df.columns = [c.strip() for c in df.columns]
                
                required = ['Category', 'House', 'Name']
                if not all(col in df.columns for col in required):
                    st.error(f"CSV needs columns: {required}")
                else:
                    st.session_state.discus_data = []
                    for _, row in df.iterrows():
                        # Create unique ID based on original data + random/index if needed
                        # using name+house is usually safe enough for a school event
                        st.session_state.discus_data.append({
                            "id": f"{row['Name']}_{row['House']}", 
                            "Category": str(row['Category']),
                            "House": str(row['House']),
                            "Name": str(row['Name']),
                            "t1": "", "t2": "", "t3": "", "t4": "", "t5": ""
                        })
                    st.session_state.finalists_generated = {}
                    st.success("Loaded!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.header("2. Add Athlete")
    with st.expander("Manual Entry"):
        m_cat = st.selectbox("Category", list(QUALIFYING_STANDARDS.keys()) + ["Other"])
        m_house = st.text_input("House")
        m_name = st.text_input("Name")
        if st.button("Add"):
            st.session_state.discus_data.append({
                "id": f"{m_name}_{m_house}",
                "Category": m_cat,
                "House": m_house,
                "Name": m_name,
                "t1": "", "t2": "", "t3": "", "t4": "", "t5": ""
            })
            st.success("Added")
            st.rerun()

# --- MAIN APP ---
st.title("Discus Manager") # <--- Title Updated

if not st.session_state.discus_data:
    st.info("Upload a CSV to begin. Format: `Category, House, Name`")
else:
    # 1. Select Category
    categories = sorted(list(set(d['Category'] for d in st.session_state.discus_data)))
    selected_cat = st.selectbox("Select Category", categories)
    
    # 2. Display Qualifying Standard
    standard = "Unknown"
    for key, val in QUALIFYING_STANDARDS.items():
        if key.lower() in selected_cat.lower():
            standard = f"{val}m"
            break
            
    st.info(f"**Qualifying Distance for {selected_cat}:** {standard} (Note: '-' = Foul)")

    # Filter Data
    cat_data = [d for d in st.session_state.discus_data if d['Category'] == selected_cat]

    # --- ROUND 1 & 2 (ALL ATHLETES) ---
    st.subheader("Phase 1: First 2 Throws")
    st.caption("You can edit names directly in the box below.")
    
    # Grid Layout for Input
    for i, athlete in enumerate(cat_data):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            # EDITABLE NAME FIELD
            # We use label_visibility="collapsed" to hide the "Name" label for a cleaner list
            new_name = st.text_input(
                "Name", 
                value=athlete['Name'], 
                key=f"name_{athlete['id']}", 
                label_visibility="collapsed"
            )
            athlete['Name'] = new_name # Update the record instantly
            st.caption(athlete['House']) # Display House underneath
            
        with c2:
            athlete['t1'] = st.text_input("Throw 1", athlete['t1'], key=f"{athlete['id']}_t1", placeholder="-")
        with c3:
            athlete['t2'] = st.text_input("Throw 2", athlete['t2'], key=f"{athlete['id']}_t2", placeholder="-")
        with c4:
            # Live calculation of current best
            best = get_best_throw(athlete)
            st.write(f"Best: **{best}**")
    
    st.divider()

    # --- THE CUT (CALCULATE TOP 5) ---
    is_final_active = st.session_state.finalists_generated.get(selected_cat, False)
    
    col_btn, col_msg = st.columns([1, 4])
    with col_btn:
        if st.button("Generate Final Round (Top 5)"):
            st.session_state.finalists_generated[selected_cat] = True
            st.rerun()

    if is_final_active:
        st.subheader("Phase 2: Final 3 Throws (Top 5 Only)")
        st.markdown("_Order is reversed: 5th place throws first, 1st place throws last._")
        
        # 1. Sort all athletes by best of first 2 throws
        sorted_athletes = sorted(cat_data, key=lambda x: get_best_throw(x), reverse=True)
        
        # 2. Take top 5
        top_5 = sorted_athletes[:5]
        
        # 3. Reverse them (Rank 5 throws first, Rank 1 throws last)
        final_order = top_5[::-1]
        
        for athlete in final_order:
            current_rank = sorted_athletes.index(athlete) + 1
            
            with st.container():
                # Highlight the leader
                bg_color = "rgba(255, 215, 0, 0.1)" if current_rank == 1 else "rgba(0,0,0,0)"
                
                c_info, c_t3, c_t4, c_t5 = st.columns([2, 1, 1, 1])
                with c_info:
                    st.markdown(f"**Rank {current_rank}: {athlete['Name']}**")
                    st.caption(f"Current Best: {get_best_throw(athlete)}m")
                with c_t3:
                    athlete['t3'] = st.text_input("Throw 3", athlete['t3'], key=f"{athlete['id']}_t3")
                with c_t4:
                    athlete['t4'] = st.text_input("Throw 4", athlete['t4'], key=f"{athlete['id']}_t4")
                with c_t5:
                    athlete['t5'] = st.text_input("Throw 5", athlete['t5'], key=f"{athlete['id']}_t5")
                st.markdown("---")

    # --- LEADERBOARD & EXPORT ---
    st.header(f"Results: {selected_cat}")
    
    # Prepare Dataframe
    results_list = []
    for athlete in cat_data:
        best = get_best_throw(athlete)
        results_list.append({
            "Name": athlete['Name'],
            "House": athlete['House'],
            "Best Throw": best,
            "T1": athlete['t1'],
            "T2": athlete['t2'],
            "T3": athlete['t3'],
            "T4": athlete['t4'],
            "T5": athlete['t5']
        })
    
    df_res = pd.DataFrame(results_list)
    
    if not df_res.empty:
        # Sort by Best Throw
        df_res = df_res.sort_values(by="Best Throw", ascending=False)
        
        # Add Rank
        df_res.reset_index(drop=True, inplace=True)
        df_res.index += 1
        df_res.index.name = "Rank"
        
        st.dataframe(df_res, use_container_width=True)
        
        # Export
        csv = df_res.to_csv().encode('utf-8')
        st.download_button(
            "Download CSV Results",
            csv,
            f"Discus_{selected_cat}.csv",
            "text/csv"
        )
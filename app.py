import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Discus Scoring App", layout="wide")
BACKUP_FILE = "discus_backup.csv"

# --- QUALIFYING DISTANCES ---
QUALIFYING_STANDARDS = {
    "Girls": 15.0, "Junior Boys": 16.0, "Intermediate": 22.0, 
    "Senior Boys": 20.0, "Senior Girls": 15.0, "Intermediate Boys": 22.0
}

# --- HELPER FUNCTIONS ---
def parse_throw(val):
    if not val or val == "" or val == "-": return 0.0
    try: return float(val)
    except ValueError: return 0.0

def get_best_throw(athlete):
    throws = [athlete.get(f't{i}', '') for i in range(1, 6)]
    valid_throws = [parse_throw(t) for t in throws]
    return max(valid_throws) if valid_throws else 0.0

def save_backup():
    """Saves current session state to a local CSV immediately."""
    if st.session_state.discus_data:
        df = pd.DataFrame(st.session_state.discus_data)
        df.to_csv(BACKUP_FILE, index=False)

def load_backup():
    """Loads data from local CSV if it exists."""
    if os.path.exists(BACKUP_FILE):
        try:
            df = pd.read_csv(BACKUP_FILE)
            # Ensure all columns exist (handle legacy backups)
            cols = ['t1','t2','t3','t4','t5']
            for c in cols:
                if c not in df.columns: df[c] = ""
            # Fill NaN with empty strings for text inputs
            df.fillna("", inplace=True)
            return df.to_dict('records')
        except Exception:
            return []
    return []

# --- STATE MANAGEMENT ---
if 'discus_data' not in st.session_state:
    # Try loading backup first
    backup_data = load_backup()
    if backup_data:
        st.session_state.discus_data = backup_data
        st.toast("Restored data from backup file!", icon="💾")
    else:
        st.session_state.discus_data = []

if 'finalists_generated' not in st.session_state:
    st.session_state.finalists_generated = {} 

# --- SIDEBAR: SETUP ---
with st.sidebar:
    st.header("1. Upload Start List")
    uploaded_file = st.file_uploader("Upload CSV (Category, House, Name)", type=['csv'])
    
    if uploaded_file:
        if st.button("Load Data (Overwrites Backup)"):
            try:
                df = pd.read_csv(uploaded_file)
                df.columns = [c.strip() for c in df.columns]
                
                st.session_state.discus_data = []
                for _, row in df.iterrows():
                    st.session_state.discus_data.append({
                        "id": f"{row['Name']}_{row['House']}", 
                        "Category": str(row['Category']),
                        "House": str(row['House']),
                        "Name": str(row['Name']),
                        "t1": "", "t2": "", "t3": "", "t4": "", "t5": ""
                    })
                save_backup() # <--- SAVE IMMEDIATELY
                st.session_state.finalists_generated = {}
                st.success("Loaded & Saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    if st.button("🗑️ Clear All Data"):
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
        st.session_state.discus_data = []
        st.rerun()

# --- MAIN APP ---
st.title("Discus Manager")

if not st.session_state.discus_data:
    st.info("Upload a CSV to begin. Data is auto-saved to 'discus_backup.csv'.")
else:
    # 1. Select Category
    categories = sorted(list(set(d['Category'] for d in st.session_state.discus_data)))
    selected_cat = st.selectbox("Select Category", categories)
    
    # Filter Data
    cat_data = [d for d in st.session_state.discus_data if d['Category'] == selected_cat]

    # --- INPUT GRID ---
    st.subheader(f"Scoring: {selected_cat}")
    
    # We use a form? No, forms prevent instant saving. We use callbacks or just script rerun.
    # Streamlit reruns the script on every interaction. We just need to save at the end of the run.
    
    for i, athlete in enumerate(cat_data):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            new_name = st.text_input("Name", value=athlete['Name'], key=f"name_{athlete['id']}", label_visibility="collapsed")
            if new_name != athlete['Name']:
                athlete['Name'] = new_name
                save_backup() # Save on name change
            st.caption(athlete['House'])
            
        with c2:
            val = st.text_input("Throw 1", athlete['t1'], key=f"{athlete['id']}_t1", placeholder="-")
            if val != athlete['t1']:
                athlete['t1'] = val
                save_backup() # Save on input change

        with c3:
            val2 = st.text_input("Throw 2", athlete['t2'], key=f"{athlete['id']}_t2", placeholder="-")
            if val2 != athlete['t2']:
                athlete['t2'] = val2
                save_backup()

        with c4:
            st.write(f"Best: **{get_best_throw(athlete)}**")

    # --- FINAL ROUND ---
    st.divider()
    col_btn, _ = st.columns([1, 4])
    # Check session state for this category's finals status
    is_final = st.session_state.finalists_generated.get(selected_cat, False)

    with col_btn:
        if st.button("Generate Final Round (Top 5)"):
            st.session_state.finalists_generated[selected_cat] = True
            st.rerun()

    if is_final:
        st.subheader("Finals (Top 5)")
        sorted_athletes = sorted(cat_data, key=lambda x: get_best_throw(x), reverse=True)
        top_5 = sorted_athletes[:5][::-1] # Top 5 reversed
        
        for athlete in top_5:
            with st.container():
                c_info, c3, c4, c5 = st.columns([2, 1, 1, 1])
                with c_info:
                    st.markdown(f"**{athlete['Name']}** ({get_best_throw(athlete)}m)")
                
                # T3
                t3 = st.text_input("T3", athlete['t3'], key=f"{athlete['id']}_t3")
                if t3 != athlete['t3']:
                    athlete['t3'] = t3
                    save_backup()
                    
                # T4
                with c4:
                    t4 = st.text_input("T4", athlete['t4'], key=f"{athlete['id']}_t4")
                    if t4 != athlete['t4']:
                        athlete['t4'] = t4
                        save_backup()
                
                # T5
                with c5:
                    t5 = st.text_input("T5", athlete['t5'], key=f"{athlete['id']}_t5")
                    if t5 != athlete['t5']:
                        athlete['t5'] = t5
                        save_backup()

    # --- EXPORT ---
    st.divider()
    # Prepare Dataframe for export
    results_list = []
    for athlete in cat_data:
        best = get_best_throw(athlete)
        results_list.append({
            "Name": athlete['Name'], "House": athlete['House'], "Best Throw": best,
            "T1": athlete['t1'], "T2": athlete['t2'], "T3": athlete['t3'], "T4": athlete['t4'], "T5": athlete['t5']
        })
    df_res = pd.DataFrame(results_list)
    if not df_res.empty:
        df_res = df_res.sort_values(by="Best Throw", ascending=False)
        csv = df_res.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, f"Discus_{selected_cat}.csv", "text/csv")

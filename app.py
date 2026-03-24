import shutil
import streamlit as st
import pandas as pd
import psutil
import os
import gc
import time
import ollama

# --- CALIBRATION DIALOG ---
@st.dialog("🎯 Calibration Complete: Update Thresholds?")
def calibration_popup(cal_df):
    st.write("Your Pro Benchmarks have been analyzed. How do you want to set your Operation sliders?")
    
    # Calculate the math from the Calibration batch
    avg_s, min_s = int(cal_df['Sharpness'].mean()), int(cal_df['Sharpness'].min())
    avg_e, min_e = int(cal_df['Exposure'].mean()), int(cal_df['Exposure'].min())
    avg_c, min_c = int(cal_df['Composition'].mean()), int(cal_df['Composition'].min())
    avg_n, min_n = int(cal_df['Narrative Score'].mean()), int(cal_df['Narrative Score'].min())
    avg_em, min_em = int(cal_df['Emotional Impact'].mean()), int(cal_df['Emotional Impact'].min())
    
    # Recalculate the required aggregate Tech Score
    avg_keeper = int((avg_s * 0.4) + (avg_e * 0.3) + (avg_c * 0.3))
    min_keeper = int((min_s * 0.4) + (min_e * 0.3) + (min_c * 0.3))
    
    c1, c2, c3 = st.columns(3)
    
    if c1.button(f"📊 Use Averages\n(e.g., Sharp: {avg_s})"):
        st.session_state.update(sl_sharp=avg_s, sl_exp=avg_e, sl_comp=avg_c, sl_narr=avg_n, sl_emo=avg_em, sl_keeper=avg_keeper, calibration_completed=False)
        st.rerun()
        
    if c2.button(f"📉 Use Minimums\n(e.g., Sharp: {min_s})"):
        st.session_state.update(sl_sharp=min_s, sl_exp=min_e, sl_comp=min_c, sl_narr=min_n, sl_emo=min_em, sl_keeper=min_keeper, calibration_completed=False)
        st.rerun()
        
    if c3.button("❌ Do Not Use"):
        st.session_state.calibration_completed = False
        st.rerun()

# Import our custom modules
from utils import send_telegram_ping, get_camera_settings, get_jpeg_files, encode_image
from ai_engine import analyze_image, categorize_photo

# --- GLOBAL CONFIG ---
GLOBAL_LEDGER_PATH = r"C:\Users\aloha\OneDrive\Apps\Codes\image_culling_tool\Hippocampus_Global_Success_Ledger.csv"

# --- CONFIGURATION & UI ---
st.set_page_config(page_title="Hippocampus 0.14.1: High Contrast", page_icon="🦛", layout="wide")

st.markdown("""
    <style>
    [data-testid='stSidebar'] { min-width: 350px; }
    div[data-testid="stMetricValue"] {
        background-color: #002b36; color: #268bd2; padding: 15px;
        border-radius: 8px; border: 2px solid #268bd2; font-weight: bold;
    }
    div[data-testid="stMetricLabel"] {
        color: #073642; font-size: 1.1rem; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL SESSION STATE ---
# --- GLOBAL SESSION STATE ---
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'last_exec_time' not in st.session_state: st.session_state.last_exec_time = "0m 0s"
if 'session_start' not in st.session_state: st.session_state.session_start = None
if 'session_batch_count' not in st.session_state: st.session_state.session_batch_count = 0

# --- NEW: Slider Memory & Pop-up Trigger ---
if 'calibration_completed' not in st.session_state: st.session_state.calibration_completed = False
if 'sl_sharp' not in st.session_state: st.session_state.sl_sharp = 70
if 'sl_exp' not in st.session_state: st.session_state.sl_exp = 60
if 'sl_comp' not in st.session_state: st.session_state.sl_comp = 60
if 'sl_narr' not in st.session_state: st.session_state.sl_narr = 70
if 'sl_emo' not in st.session_state: st.session_state.sl_emo = 60
if 'sl_keeper' not in st.session_state: st.session_state.sl_keeper = 71

# --- SIDEBAR: COMMAND CENTER ---
with st.sidebar:
    st.header("🎛️ Command Center v0.14.1")
    if st.button("📡 Test Telegram Link"):
        with st.spinner("Pinging..."):
            if send_telegram_ping("🦛 *Ping!* Secure connection confirmed."): st.success("Linked!")
            else: st.error("Link Failed. Check secrets.toml")
    
    st.divider()
    is_locked = st.session_state.is_running
    folder_path = st.text_input("📁 Source Folder:", value=r"C:\Users\aloha\TestPhotos", disabled=is_locked)
    op_mode = st.radio("🛠️ System Mode:", ["Operation (My Work)", "Calibration (Pro Benchmarks)"], disabled=is_locked)
    
    st.divider()
    st.subheader("🎯 Quantitative Thresholds")
    c1, c2 = st.columns(2)
    
    # Sliders now read and write directly to the session_state keys
    min_sharp = c1.slider("Sharpness", 0, 100, key='sl_sharp', disabled=is_locked)
    min_exp = c2.slider("Exposure", 0, 100, key='sl_exp', disabled=is_locked)
    min_comp = c1.slider("Composition", 0, 100, key='sl_comp', disabled=is_locked)
    min_narrative = c2.slider("Narrative", 0, 100, key='sl_narr', disabled=is_locked)
    min_emotional = c1.slider("Emotional Impact", 0, 100, key='sl_emo', disabled=is_locked)
    
    keeper_threshold = st.slider("Min Aggregate Tech Score", 0, 100, key='sl_keeper', disabled=is_locked)

# --- MAIN ENGINE ---
st.title(f"🦛 Hippocampus: {op_mode}")

v_col1, v_col2, v_col3 = st.columns(3)
cpu_meter = v_col1.empty()
ram_meter = v_col2.empty()
timer_meter = v_col3.empty()

cpu_meter.metric("CPU Load", f"{psutil.cpu_percent()}%")
ram_meter.metric("RAM Usage", f"{psutil.virtual_memory().percent}%")
timer_meter.metric("⏱️ Timer", st.session_state.last_exec_time)

if folder_path and os.path.isdir(folder_path):
    files = get_jpeg_files(folder_path)
    report_path = os.path.join(folder_path, "_Hippocampus_Grand_Master_Report.csv")
    
    if os.path.exists(report_path): master_df = pd.read_csv(report_path)
    else: # --- NEW: Added Emotional Impact to columns ---
        master_df = pd.DataFrame(columns=["Filename", "Mode", "Focal Length", "Aperture", "Tech Score", "Narrative Score", "Emotional Impact", "AI Category", "Competition Status", "Sharpness", "Exposure", "Composition", "Chinny Roast", "WSCT Trading", "Privacy Alert", "Raw Reply"])

    processed_in_mode = set(master_df[master_df['Mode'] == op_mode]['Filename'])
    files_to_process = [f for f in files if f not in processed_in_mode]

    if not st.session_state.is_running:
        st.write(f"📂 **Total Found:** {len(files)} | **Remaining:** {len(files_to_process)}")
        if st.button("🚀 INITIATE ANALYSIS", type="primary") and files_to_process:
            st.session_state.update(is_running=True, session_start=time.time(), session_batch_count=0)
            st.rerun()
    else:
        if st.button("🛑 EMERGENCY HALT", type="primary"):
            # --- THE FIX: Send the Telegram report BEFORE pulling the plug ---
            if st.session_state.session_batch_count > 0:
                df_session = master_df[master_df['Mode'] == op_mode].tail(st.session_state.session_batch_count)
                keepers = len(df_session[df_session['AI Category'] == 'Keeper'])
                best_shot = df_session.loc[df_session['Tech Score'].idxmax()]['Filename'] if not df_session.empty else "N/A"
                
                tele_msg = (f"🦛 *Hippocampus HALTED*\n"
                            f"📸 *Processed:* {st.session_state.session_batch_count}\n"
                            f"🏆 *Keepers:* {keepers} ({int((keepers/st.session_state.session_batch_count)*100)}% Yield)\n"
                            f"⏱️ *Time:* {st.session_state.last_exec_time}\n"
                            f"🌟 *Top Technical:* `{best_shot}`")
                send_telegram_ping(tele_msg)
            
            # Now safely reset the system
            st.session_state.is_running = False
            st.rerun()

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            for i, f in enumerate(files_to_process):
                if not st.session_state.is_running: break
                
                filepath = os.path.join(folder_path, f)
                status_text.text(f"Scanning {f}... ({i+1}/{len(files_to_process)})")

                try:
                    # Replace the old base_64 and focal length logic with this:
                    base64_img = encode_image(filepath)
                    metrics = analyze_image(base64_img, op_mode)
                    # --- UPDATED: Pass min_emotional to the brain ---
                    cat = categorize_photo(metrics, min_sharp, min_exp, min_comp, keeper_threshold, min_narrative, min_emotional)
                    focal, ap = get_camera_settings(filepath)
                    
                    # --- NEW: Save Emotional Impact to the row ---
                    new_row = pd.DataFrame([{
                        "Filename": f, "Mode": op_mode, "Focal Length": focal, "Aperture": ap,
                        "Tech Score": metrics['Tech Score'], "Narrative Score": metrics['Narrative Score'], 
                        "Emotional Impact": metrics['Emotional Impact'], "AI Category": cat,
                        "Competition Status": metrics['Competition Status'], "Sharpness": metrics['Sharpness'], 
                        "Exposure": metrics['Exposure'], "Composition": metrics['Composition'],
                        "Chinny Roast": metrics['Chinny Roast'], "WSCT Trading": 0, 
                        "Privacy Alert": metrics['Privacy Alert'], "Raw Reply": metrics['Raw Reply']
                    }])
                    
                    master_df = pd.concat([master_df, new_row], ignore_index=True).drop_duplicates(subset=['Filename', 'Mode'], keep='last')
                    master_df.to_csv(report_path, index=False)
                    st.session_state.session_batch_count += 1

                except Exception as ex: 
                    st.error(f"Hardware Error on {f}: {ex}")

                # UPDATE UI
                progress_bar.progress((i + 1) / len(files_to_process))
                elapsed = time.time() - st.session_state.session_start
                st.session_state.last_exec_time = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
                
                cpu_meter.metric("CPU Load", f"{psutil.cpu_percent()}%")
                timer_meter.metric("⏱️ Timer", st.session_state.last_exec_time)

        finally:
            # --- CLEANED UP FINALLY BLOCK ---
            if st.session_state.session_batch_count > 0:
                # 1. Trigger the Pop-up if in Calibration Mode
                if op_mode == "Calibration (Pro Benchmarks)":
                    st.session_state.calibration_completed = True
                    
                # 2. Grab the session data
                df_session = master_df[master_df['Mode'] == op_mode].tail(st.session_state.session_batch_count)
                keepers = len(df_session[df_session['AI Category'].str.contains('Keeper', na=False)])
                best_shot = df_session.loc[df_session['Tech Score'].idxmax()]['Filename'] if not df_session.empty else "N/A"
                
                # 3. Update Global Ledger
                os.makedirs(os.path.dirname(GLOBAL_LEDGER_PATH), exist_ok=True)
                successful_batch = df_session[df_session['Tech Score'] >= keeper_threshold]
                
                if not successful_batch.empty:
                    if os.path.exists(GLOBAL_LEDGER_PATH):
                        global_df = pd.read_csv(GLOBAL_LEDGER_PATH)
                        global_df = pd.concat([global_df, successful_batch], ignore_index=True)
                    else:
                        global_df = successful_batch.copy()
                    
                    global_df.drop_duplicates(subset=['Filename'], keep='last', inplace=True)
                    global_df.to_csv(GLOBAL_LEDGER_PATH, index=False)
                
                # 4. Send Telegram Message
                tele_msg = (f"🦛 *Hippocampus Update*\n📸 *Processed:* {st.session_state.session_batch_count}\n"
                            f"🏆 *Keepers:* {keepers} ({int((keepers/st.session_state.session_batch_count)*100)}% Yield)\n"
                            f"⏱️ *Time:* {st.session_state.last_exec_time}\n🌟 *Top Technical:* `{best_shot}`")
                send_telegram_ping(tele_msg)
            
            # 5. Safely shut down the AI and reset
            try: ollama.generate(model='llava-phi3', prompt='', keep_alive=0)
            except: pass
            
            st.session_state.is_running = False
            gc.collect()
            st.rerun()
    
    # --- TRIGGER CALIBRATION POP-UP ---
    if st.session_state.calibration_completed:
        cal_df = master_df[master_df['Mode'] == 'Calibration (Pro Benchmarks)']
        if not cal_df.empty:
            calibration_popup(cal_df)

    # --- DASHBOARD ---
    df_dash = master_df[master_df['Mode'] == op_mode]
    if not df_dash.empty:
        st.divider()
        st.subheader("📊 Tactical Overview (6-Tier Curation)")
        
        # Row 1: The Winning Tiers
        k_cols = st.columns(4)
        k_cols[0].metric("🌟 Masterpiece", len(df_dash[df_dash['AI Category'] == 'Keeper_Masterpiece']))
        k_cols[1].metric("📖 Storyteller", len(df_dash[df_dash['AI Category'] == 'Keeper_Storyteller']))
        k_cols[2].metric("🎨 Mood", len(df_dash[df_dash['AI Category'] == 'Keeper_Mood']))
        k_cols[3].metric("⚙️ Technical", len(df_dash[df_dash['AI Category'] == 'Keeper_Technical']))
        
        # Row 2: Operations
        st.write("") # Spacer
        o_cols = st.columns(3)
        o_cols[0].metric("🕶️ Review", len(df_dash[df_dash['AI Category'] == 'Review']))
        o_cols[1].metric("🗑️ Discarded", len(df_dash[df_dash['AI Category'] == 'Discard']))
        o_cols[2].metric("⏱️ Session", st.session_state.last_exec_time)
        
        styled_df = df_dash[["Filename", "Tech Score", "Narrative Score", "Emotional Impact", "AI Category"]].tail(15).style.background_gradient(subset=['Tech Score', 'Narrative Score', 'Emotional Impact'], cmap='RdYlGn', vmin=0, vmax=100)
        st.dataframe(styled_df, use_container_width=True)

        if st.button("🏗️ PHYSICAL DEPLOY"):
            category_map = {
                "Keeper_Masterpiece": "1_Masterpiece", 
                "Keeper_Storyteller": "2_Storyteller", 
                "Keeper_Mood": "3_Mood", 
                "Keeper_Technical": "4_Technical", 
                "Review": "Review_Needed", 
                "Discard": "Discarded"
            }
            
            for folder in category_map.values(): os.makedirs(os.path.join(folder_path, folder), exist_ok=True)
            for _, row in df_dash.iterrows():
                src = os.path.join(folder_path, row['Filename'])
                if os.path.isfile(src): shutil.move(src, os.path.join(folder_path, category_map[row['AI Category']], row['Filename']))
            st.success("🏁 Files deployed.")
            st.balloons()

    # --- NEW: ALL-TIME HARDWARE INSIGHTS ---
        st.subheader("🏆 Lifetime Hardware Insights (Your Global Top Gear)")
        
        if os.path.exists(GLOBAL_LEDGER_PATH):
            global_df = pd.read_csv(GLOBAL_LEDGER_PATH)
            hw_c1, hw_c2 = st.columns(2)
            
            valid_focal = global_df[global_df['Focal Length'] != 'Unknown']['Focal Length']
            if not valid_focal.empty:
                hw_c1.write("**All-Time Top Focal Lengths**")
                hw_c1.dataframe(valid_focal.value_counts().head(5), use_container_width=True)
            else: hw_c1.write("No Focal Length data logged yet.")
            
            if 'Aperture' in global_df.columns:
                valid_aperture = global_df[global_df['Aperture'] != 'Unknown']['Aperture']
                if not valid_aperture.empty:
                    hw_c2.write("**All-Time Top Apertures (F-Stops)**")
                    hw_c2.dataframe(valid_aperture.value_counts().head(5), use_container_width=True)
                else: hw_c2.write("No Aperture data logged yet.")
        else:
            st.info("The Global Success Ledger is empty. Process some Keepers to start tracking your lifetime gear stats!")
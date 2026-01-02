# --- 1. SQLITE FIX FOR STREAMLIT CLOUD (CRITICAL) ---
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components 
import time
from fpdf import FPDF

# --- 2. CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

st.set_page_config(
    page_title="InsightGen Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend (Safe Loader)
try:
    from agents import planner, coder, reporter, DEMO_MODE, debug_error
    import tools
except Exception as e:
    DEMO_MODE = True
    tools = None
    planner = coder = reporter = None
    debug_error = f"CRITICAL IMPORT FAILURE: {e}"

# --- 3. SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_plot" not in st.session_state:
    st.session_state.analysis_plot = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- 4. PDF ENGINE ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        # BRANDING UPDATE: InsightGen
        self.cell(0, 10, 'InsightGen: Intelligence Report', 0, 1, 'C')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(report_type, df_stats, query=None, ai_text=None, plot_path=None, dashboard_imgs=None):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    if report_type == "full":
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "1. Executive AI Analysis", 0, 1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"Query: {query}", 0, 1)
        pdf.set_font("Arial", size=10)
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(5)
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=170)
        pdf.add_page()

    pdf.set_font("Arial", 'B', 14)
    title = "2. Automated Data Dashboard" if report_type == "full" else "Automated Dashboard Report"
    pdf.cell(0, 10, title, 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Statistical Summary:", 0, 1)
    pdf.set_font("Courier", size=8)
    stats_str = df_stats.to_string()
    pdf.multi_cell(0, 5, stats_str)
    pdf.ln(10)

    if dashboard_imgs:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Visual Analytics:", 0, 1)
        pdf.ln(5)
        for img_path in dashboard_imgs:
            if os.path.exists(img_path):
                pdf.image(img_path, x=10, w=180)
                pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INSIGHTGEN SCI-FI THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    
    /* GLOBAL STYLES */
    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif;
        color: #E0E0E0; 
        background-color: #020a13;
        font-size: 18px;
    }
    
    /* BACKGROUND GRID (Holographic effect) */
    .stApp {
        background-color: #020a13;
        background-image: 
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px; 
    }

    /* SCROLLBARS */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #020a13; }
    ::-webkit-scrollbar-thumb { background: #00F0FF; border-radius: 4px; }
    
    /* HEADERS */
    .main-title {
        font-family: 'Orbitron', sans-serif;
        color: #00F0FF;
        font-size: 4.5rem;
        line-height: 1;
        text-shadow: 0 0 15px rgba(0, 240, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 3px;
    }
    h1, h2, h3 { 
        font-family: 'Orbitron', sans-serif !important; 
        color: #00F0FF !important; 
        text-transform: uppercase; 
        text-shadow: 0 0 5px rgba(0, 240, 255, 0.4);
    }

    /* METRIC CARDS (Glassmorphism) */
    .metric-card {
        background: rgba(0, 20, 40, 0.6);
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-left: 3px solid #00F0FF;
        padding: 15px;
        text-align: center;
        backdrop-filter: blur(5px);
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.1);
        border-radius: 5px;
        transition: transform 0.3s;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #00F0FF; }
    
    .metric-value { 
        font-family: 'Orbitron', sans-serif; 
        font-size: 42px; 
        color: #FFFFFF; 
        text-shadow: 0 0 10px #00F0FF; 
    }
    .metric-label { 
        font-size: 14px; 
        color: #00F0FF; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        font-weight: 700;
    }

    /* BUTTONS */
    .stButton>button {
        background: linear-gradient(90deg, #001f3f, #003366);
        color: #00F0FF;
        font-family: 'Orbitron', sans-serif;
        font-size: 16px;
        border: 1px solid #00F0FF;
        border-radius: 5px; 
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }
    .stButton>button:hover { 
        background: #00F0FF; 
        color: #020a13; 
        box-shadow: 0 0 20px #00F0FF; 
        font-weight: bold;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: none; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: rgba(0, 20, 40, 0.6); 
        border: 1px solid rgba(0, 240, 255, 0.3); 
        color: #888; 
        font-family: 'Orbitron', sans-serif; 
        border-radius: 5px 5px 0 0; 
    }
    .stTabs [aria-selected="true"] { 
        background-color: rgba(0, 240, 255, 0.1); 
        color: #00F0FF; 
        border: 1px solid #00F0FF; 
        border-bottom: none;
        box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.2);
    }
    
    /* DATAFRAME & INPUTS */
    div[data-testid="stDataFrame"] { border: 1px solid #00F0FF; border-radius: 5px; }
    input[type="text"] { 
        background-color: #05101a !important; 
        color: #00F0FF !important; 
        border: 1px solid #00F0FF !important; 
        font-family: 'Rajdhani', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### > SYSTEM_CONFIG")
    uploaded_file = st.file_uploader("UPLOAD DATA SOURCE", type=["csv", "xlsx"])
    st.markdown("---")
    
    # 🟢 DEBUGGER
    if DEMO_MODE:
        st.code("STATUS: OFFLINE (SIMULATION)")
        st.error(f"Reason: {debug_error}")
        if "API Key Missing" in str(debug_error):
            st.warning("Check 'Secrets' in Streamlit Settings.")
    else:
        st.code("STATUS: ONLINE (CONNECTED)")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    # BRANDING UPDATE
    st.caption("INSIGHTGEN UI | V1.3 (SCIFI)")

# --- 7. MAIN CONTENT ---
# BRANDING UPDATE: Main Title
st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)
st.markdown("#### *// INITIALIZING INTELLIGENCE PROTOCOLS...*")

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        if tools: tools.df = df
        df.to_csv("dataset.csv", index=False)

        # METRICS GRID
        st.write("")
        st.subheader("> DATA_DIAGNOSTICS")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[0]}</div><div class="metric-label">ROWS</div></div>""", unsafe_allow_html=True)
        with mc2: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[1]}</div><div class="metric-label">COLUMNS</div></div>""", unsafe_allow_html=True)
        with mc3: 
            missing = df.isnull().sum().sum(); color = "#FF0055" if missing > 0 else "#00F0FF"
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: {color}">{missing}</div><div class="metric-label">MISSING</div></div>""", unsafe_allow_html=True)
        with mc4: 
            dupes = df.duplicated().sum()
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">DUPLICATES</div></div>""", unsafe_allow_html=True)
        st.write("")

        tab1, tab2 = st.tabs(["[ 1. INTELLIGENCE_HUB ]", "[ 2. VISUAL_DASHBOARD ]"])

        # --- TAB 1 ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ENTER COMMAND:", placeholder="> Analyze correlation between X and Y...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("EXECUTE", use_container_width=True)

            if run_btn and query:
                st.session_state.last_query = query
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe("https://lottie.host/embed/55a2fae6-5d47-4ada-b1fe-1b2e52f5c56d/RpgXLM6mwe.lottie", height=200, scrolling=False)
                        st.markdown("<center style='color: #00F0FF; font-family: Orbitron;'>[ PROCESSING DATA... ]</center>", unsafe_allow_html=True)

                try:
                    if DEMO_MODE:
                        time.sleep(4) 
                        loader.empty()
                        st.session_state.analysis_result = f"Query: {query}\nStatus: SIMULATED RESPONSE\nReason: {debug_error}\n1. Trend Detected: Positive.\n2. Correlation: Strong (0.85)."
                        st.session_state.analysis_plot = "simulated"
                    else:
                        if os.path.exists("plot.png"): os.remove("plot.png")
                        
                        from crewai import Crew, Task, Process
                        from agents import planner, coder, reporter 
                        
                        task_plan = Task(
                            description=f"Create a plan to analyze: '{query}'", 
                            expected_output="Step-by-step plan", 
                            agent=planner
                        )
                        task_code = Task(
                            description="Execute the plan. PRINT ALL RESULTS. Save 'plot.png' if needed.", 
                            expected_output="Execution Logs with Numbers", 
                            agent=coder, 
                            context=[task_plan]
                        )
                        task_report = Task(
                            description="Summarize the findings from the code logs.", 
                            expected_output="Data-driven Summary", 
                            agent=reporter, 
                            context=[task_code]
                        )
                        
                        crew = Crew(
                            agents=[planner, coder, reporter], 
                            tasks=[task_plan, task_code, task_report], 
                            process=Process.sequential, 
                            verbose=True
                        )
                        
                        result = crew.kickoff()
                        loader.empty()
                        st.session_state.analysis_result = str(result)
                        st.session_state.analysis_plot = "plot.png" if os.path.exists("plot.png") else None
                except Exception as e:
                    loader.empty()
                    st.error(f"RUNTIME ERROR: {e}")

            if st.session_state.analysis_result:
                st.markdown("---")
                st.caption(f"LAST COMMAND: {st.session_state.last_query}")
                r1, r2 = st.columns([1.5, 1])
                with r1:
                    st.markdown("### > ANALYSIS_LOG")
                    st.markdown(st.session_state.analysis_result)
                with r2:
                    st.markdown("### > VISUAL_FEED")
                    if st.session_state.analysis_plot == "simulated":
                        st.info("Simulated Plot")
                    elif st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png"):
                        st.image("plot.png")
                    else:
                        st.caption("NO_IMAGE_GENERATED")

        # --- TAB 2 ---
        with tab2:
            st.write("")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1: selected_cat = st.selectbox("SELECT FILTER", cat_cols)
                with col_f2: unique_vals = df[selected_cat].unique(); selected_val = st.multiselect(f"FILTER VALUES", unique_vals, default=unique_vals[:5])
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df

            dashboard_images = []
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            if not numeric_df.empty:
                # CORRELATION (TEAL THEME)
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Teal', template="plotly_dark")
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00F0FF")
                try:
                    fig_corr.write_image("dash_corr.png")
                    dashboard_images.append("dash_corr.png")
                except: pass
                
                # HISTOGRAM (CYAN THEME)
                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_dark")
                fig1.update_traces(marker_color='#00F0FF', marker_line_color='#003366')
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00F0FF")
                try:
                    fig1.write_image("dash_hist.png")
                    dashboard_images.append("dash_hist.png")
                except: pass

                # SCATTER (BLUE THEME)
                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_dark")
                fig2.update_traces(marker_color='#0077BE')
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00F0FF")
                try:
                    fig2.write_image("dash_scatter.png")
                    dashboard_images.append("dash_scatter.png")
                except: pass

            d_col1, d_col2 = st.columns([4, 1])
            with d_col1: st.markdown(f"**Live Records:** {len(filtered_df)}") 
            with d_col2:
                try:
                    stats_summary = df.describe()
                    dash_pdf = generate_pdf("dashboard", stats_summary, dashboard_imgs=dashboard_images)
                    # BRANDING UPDATE: Filename
                    st.download_button(label="[ DOWNLOAD_DASHBOARD ]", data=dash_pdf, file_name="InsightGen_Dashboard.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"PDF Gen Error: {e}")

            st.markdown("---")
            column_config = {}
            for col in filtered_df.select_dtypes(include="number").columns:
                column_config[col] = st.column_config.ProgressColumn(col, format="%.2f", min_value=float(filtered_df[col].min()), max_value=float(filtered_df[col].max()))
            st.dataframe(filtered_df.head(100), width="stretch", height=300, column_config=column_config)
            
            st.markdown("---")
            if not numeric_df.empty:
                st.markdown("### > VISUAL_ANALYTICS_HUB")
                st.plotly_chart(fig_corr, width="stretch")
                gc1, gc2 = st.columns(2)
                with gc1: st.plotly_chart(fig1, width="stretch")
                with gc2: st.plotly_chart(fig2, width="stretch")
            else:
                st.info("NO_NUMERIC_DATA")

        with full_report_container:
            if st.session_state.analysis_result:
                plot_to_use = "plot.png" if st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png") else None
                stats_summary = filtered_df.describe()
                try:
                    full_pdf = generate_pdf("full", stats_summary, st.session_state.last_query, str(st.session_state.analysis_result), plot_to_use, dashboard_images)
                    # BRANDING UPDATE: Filename
                    st.download_button(label="[ DOWNLOAD_FULL_REPORT ]", data=full_pdf, file_name="InsightGen_Full_Report.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"Full PDF Error: {e}")

    except Exception as e:
        st.error(f"FATAL_ERROR: {e}")
else:
    with st.container():
        st.warning("SYSTEM STANDBY: AWAITING DATA UPLOAD...")

# --- 1. SQLITE FIX FOR STREAMLIT CLOUD (MUST BE AT THE VERY TOP) ---
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
import tempfile

# --- 2. SETUP & CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

st.set_page_config(
    page_title="InsightGen Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend (Safely)
try:
    from agents import planner, coder, reporter, DEMO_MODE
    import tools
except ImportError:
    DEMO_MODE = True
    tools = None

# --- 3. INITIALIZE MEMORY BANK ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_plot" not in st.session_state:
    st.session_state.analysis_plot = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- 4. PDF GENERATOR ENGINE ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
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
    
    # --- A. FULL AI REPORT ---
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

    # --- B. DASHBOARD STATS & CHARTS ---
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

# --- 5. MATRIX THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Share Tech Mono', monospace;
        color: #00FF41; 
        background-color: #0D0208;
        font-size: 16px;
    }
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 255, 65, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 65, 0.03) 1px, transparent 1px);
        background-size: 20px 20px; 
    }
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #003B00; border: 1px solid #00FF41; }
    
    .main-title {
        font-family: 'VT323', monospace;
        color: #00FF41;
        font-size: 5rem;
        line-height: 1;
        text-shadow: 2px 2px 0px #003B00;
        letter-spacing: -2px;
        text-transform: uppercase;
    }
    h1, h2, h3 { font-family: 'VT323', monospace !important; color: #00FF41 !important; text-transform: uppercase; }

    .metric-card {
        background-color: #000;
        border: 1px solid #00FF41;
        padding: 15px;
        text-align: center;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
    }
    .metric-value { font-family: 'VT323', monospace; font-size: 42px; color: #00FF41; text-shadow: 0 0 5px #00FF41; }
    .metric-label { font-size: 14px; color: #008F11; text-transform: uppercase; letter-spacing: 2px; }

    .stButton>button {
        background-color: #000000;
        color: #00FF41;
        font-family: 'Share Tech Mono', monospace;
        font-size: 18px;
        border: 2px solid #00FF41;
        border-radius: 0px; 
        text-transform: uppercase;
    }
    .stButton>button:hover { background-color: #00FF41; color: #000000; box-shadow: 0 0 15px #00FF41; }

    .stTabs [data-baseweb="tab-list"] { gap: 0px; border-bottom: 2px solid #003B00; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #000; border: 1px solid #003B00; color: #003B00; font-family: 'Share Tech Mono', monospace; border-radius: 0px; }
    .stTabs [aria-selected="true"] { background-color: #001100; color: #00FF41; border: 1px solid #00FF41; border-bottom: none; }
    
    div[data-testid="stDataFrame"] { border: 1px solid #00FF41; font-family: 'Share Tech Mono', monospace; }
    input[type="text"] { background-color: #000 !important; color: #00FF41 !important; border: 1px solid #00FF41 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### > SYSTEM_CONFIG")
    uploaded_file = st.file_uploader("UPLOAD DATA SOURCE", type=["csv", "xlsx"])
    
    st.markdown("---")
    if DEMO_MODE:
        st.code("STATUS: OFFLINE (SIMULATION)")
        st.caption("Error: Check API Key or Libraries")
    else:
        st.code("STATUS: ONLINE (CONNECTED)")
        
    st.markdown("---")
    
    # 🟢 FULL REPORT CONTAINER
    full_report_container = st.container()

    st.markdown("---")
    st.caption("TERMINAL_V8.0 | CLOUD PATCHED")

# --- 7. MAIN CONTENT ---
st.markdown("<div class='main-title'>INSIGHT_GEN</div>", unsafe_allow_html=True)
st.markdown("#### *// EXECUTING AUTONOMOUS DATA PROTOCOLS...*")

if uploaded_file:
    # A. LOAD DATA
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        if tools: tools.df = df
        df.to_csv("dataset.csv", index=False)

        # B. METRICS GRID
        st.write("")
        st.subheader("> SYSTEM_METRICS")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[0]}</div><div class="metric-label">ROWS_LOADED</div></div>""", unsafe_allow_html=True)
        with mc2: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[1]}</div><div class="metric-label">VARIABLES</div></div>""", unsafe_allow_html=True)
        with mc3: 
            missing = df.isnull().sum().sum(); color = "#FF0000" if missing > 0 else "#00FF41"
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: {color}">{missing}</div><div class="metric-label">ERRORS_NULL</div></div>""", unsafe_allow_html=True)
        with mc4: 
            dupes = df.duplicated().sum()
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">DUPLICATES</div></div>""", unsafe_allow_html=True)
        st.write("")

        # C. TABS INTERFACE
        tab1, tab2 = st.tabs(["[ 1. AGENT_TERMINAL ]", "[ 2. AUTO_DASHBOARD ]"])

        # --- TAB 1: AGENT WORKFLOW ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ENTER QUERY COMMAND:", placeholder="> Analyze sales trends...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("RUN_SCRIPT.EXE", use_container_width=True)

            if run_btn and query:
                st.session_state.last_query = query
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe("https://lottie.host/embed/705a9879-1c4b-45a1-b1ee-d7690f56f458/HMMnGjpbaU.lottie", height=200, scrolling=False)
                        st.markdown("<center style='color: #00FF41;'>[ PROCESSING... ]</center>", unsafe_allow_html=True)

                try:
                    if DEMO_MODE:
                        time.sleep(4) 
                        loader.empty()
                        st.session_state.analysis_result = f"Query: {query}\nStatus: SIMULATED RESPONSE\n1. Trend Detected: Positive.\n2. Correlation: Strong (0.85)."
                        st.session_state.analysis_plot = "simulated"
                    else:
                        # 🟢 CLEANUP OLD PLOT
                        if os.path.exists("plot.png"):
                            os.remove("plot.png")
                            
                        from crewai import Crew, Task, Process
                        from agents import planner, coder, reporter 
                        task_plan = Task(description=f"Create Python plan for: '{query}'", expected_output="Step list", agent=planner)
                        task_code = Task(description="Execute plan. Save 'plot.png'.", expected_output="Numbers", agent=coder, context=[task_plan])
                        task_report = Task(description="Summarize findings.", expected_output="Summary", agent=reporter, context=[task_code])
                        crew = Crew(agents=[planner, coder, reporter], tasks=[task_plan, task_code, task_report], process=Process.sequential, verbose=True)
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
                    st.markdown("#### > EXEC_SUMMARY")
                    st.markdown(st.session_state.analysis_result)
                with r2:
                    st.markdown("#### > VISUAL_OUTPUT")
                    if st.session_state.analysis_plot == "simulated":
                        st.info("Simulated Plot")
                    elif st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png"):
                        st.image("plot.png")
                    else:
                        st.caption("NO_IMAGE_GENERATED")

        # --- TAB 2: AUTOMATED DASHBOARD ---
        with tab2:
            st.write("")
            st.markdown("#### > DATA_FILTERS")
            
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1: selected_cat = st.selectbox("SELECT PARAMETER", cat_cols)
                with col_f2: unique_vals = df[selected_cat].unique(); selected_val = st.multiselect(f"SELECT VALUES", unique_vals, default=unique_vals[:5])
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df

            # 🟢 GENERATE DASHBOARD CHARTS
            dashboard_images = []
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Greens', template="plotly_dark")
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                try:
                    fig_corr.write_image("dash_corr.png")
                    dashboard_images.append("dash_corr.png")
                except: pass

                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_dark")
                fig1.update_traces(marker_color='#00FF41', marker_line_color='#003B00')
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                try:
                    fig1.write_image("dash_hist.png")
                    dashboard_images.append("dash_hist.png")
                except: pass

                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_dark")
                fig2.update_traces(marker_color='#008F11')
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                try:
                    fig2.write_image("dash_scatter.png")
                    dashboard_images.append("dash_scatter.png")
                except: pass

            d_col1, d_col2 = st.columns([4, 1])
            with d_col1: 
                st.markdown(f"**Live Records:** {len(filtered_df)}") 
            with d_col2:
                try:
                    stats_summary = df.describe()
                    dash_pdf = generate_pdf("dashboard", stats_summary, dashboard_imgs=dashboard_images)
                    st.download_button(
                        label="[ DOWNLOAD_DASHBOARD.PDF ]",
                        data=dash_pdf,
                        file_name="Dashboard_Visuals.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF Gen Error: {e}")

            st.markdown("---")
            st.markdown("#### > LIVE_DATA_FEED")
            column_config = {}
            for col in filtered_df.select_dtypes(include="number").columns:
                column_config[col] = st.column_config.ProgressColumn(col, format="%.2f", min_value=float(filtered_df[col].min()), max_value=float(filtered_df[col].max()))
            st.dataframe(filtered_df.head(100), use_container_width=True, height=300, column_config=column_config)
            
            st.markdown("---")
            if not numeric_df.empty:
                st.markdown("#### > VISUAL_ANALYTICS_HUB")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                gc1, gc2 = st.columns(2)
                with gc1: st.plotly_chart(fig1, use_container_width=True)
                with gc2: st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("NO_NUMERIC_DATA")

        # 🟢 SIDEBAR: FULL REPORT
        with full_report_container:
            if st.session_state.analysis_result:
                plot_to_use = "plot.png" if st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png") else None
                stats_summary = filtered_df.describe()
                
                try:
                    full_pdf = generate_pdf("full", stats_summary, st.session_state.last_query, str(st.session_state.analysis_result), plot_to_use, dashboard_images)
                    st.download_button(
                        label="[ DOWNLOAD_FULL_REPORT.PDF ]",
                        data=full_pdf,
                        file_name="InsightGen_Full_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Full PDF Error: {e}")

    except Exception as e:
        st.error(f"FATAL_ERROR: {e}")

else:
    with st.container():
        st.warning("SYSTEM STANDBY: AWAITING DATA UPLOAD...")

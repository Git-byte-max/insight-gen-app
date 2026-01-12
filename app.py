import os
import sys

# --- CRITICAL FIX: DISABLE TELEMETRY AT THE ENTRY POINT ---
# This MUST be the first thing the app does to prevent the crash.
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# --- SQLITE FIX FOR STREAMLIT CLOUD ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components 
import time
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(
    page_title="INSIGHTGEN: Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend
try:
    # We import tools first to ensure df is linked
    import tools
    from agents import planner, coder, reporter, DEMO_MODE, debug_error
except Exception as e:
    st.error(f"Backend Import Error: {e}")
    DEMO_MODE = True
    tools = None
    planner = coder = reporter = None
    debug_error = f"System Error: {e}"

# --- SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_plot" not in st.session_state:
    st.session_state.analysis_plot = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- ADVANCED PDF ENGINE ---
class PDFReport(FPDF):
    def header(self):
        # MAROON HEADER BAR
        self.set_fill_color(128, 0, 0) # Maroon
        self.rect(0, 0, 210, 30, 'F')
        
        # WHITE SERIF TITLE
        self.set_font('Times', 'B', 20)
        self.set_text_color(255, 255, 255) 
        self.set_y(10)
        self.cell(0, 10, 'INSIGHTGEN | ANALYTICS REPORT', 0, 1, 'C')
        
        # SUBTITLE
        self.set_font('Arial', '', 10) 
        self.set_text_color(240, 240, 230) 
        self.cell(0, 0, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, f'Confidential // Page {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Times', 'B', 16)
        self.set_text_color(28, 28, 28) 
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        # Maroon Underline
        self.set_draw_color(128, 0, 0)
        self.set_line_width(1)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def create_table(self, df):
        """ Renders a 'Printed' Style Table """
        self.set_font("Arial", "B", 9)
        self.set_fill_color(245, 245, 240) 
        self.set_text_color(0, 0, 0)
        self.set_draw_color(200, 200, 200) 
        
        # Headers
        col_width = 190 / (len(df.columns) + 1)
        self.cell(col_width, 8, "Metric", 1, 0, 'C', 1)
        for col in df.columns:
            self.cell(col_width, 8, str(col)[:10], 1, 0, 'C', 1)
        self.ln()
        
        # Data Rows
        self.set_font("Arial", "", 9)
        for index, row in df.iterrows():
            self.cell(col_width, 8, str(index), 1, 0, 'C')
            for val in row:
                try:
                    val_str = f"{val:.2f}" if isinstance(val, float) else str(val)
                except:
                    val_str = str(val)
                self.cell(col_width, 8, val_str, 1, 0, 'C')
            self.ln()

def generate_pdf(report_type, df, query=None, ai_text=None, plot_path=None, dashboard_imgs=None):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- SECTION 1: MISSION OVERVIEW ---
    pdf.section_title("1. Mission Overview")
    
    rows = df.shape[0]
    cols = df.shape[1]
    missing = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    
    # 2x2 Data Grid
    pdf.set_font("Arial", '', 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(200, 200, 200)
    
    # Row 1
    pdf.cell(95, 12, f" Total Records: {rows}", 1, 0, 'L', 1)
    pdf.cell(95, 12, f" Variables: {cols}", 1, 1, 'L', 1)
    # Row 2
    pdf.cell(95, 12, f" Missing Data: {missing}", 1, 0, 'L', 1)
    pdf.cell(95, 12, f" Duplicates: {dupes}", 1, 1, 'L', 1)
    pdf.ln(10)

    # --- SECTION 2: EXECUTIVE SUMMARY ---
    if report_type == "full":
        pdf.section_title("2. Intelligence Report")
        pdf.set_font("Times", 'B', 11)
        pdf.cell(0, 8, f"QUERY SCOPE: {query}", 0, 1)
        
        pdf.set_font("Arial", '', 10)
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(10)
        
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=190)
            pdf.ln(10)
        pdf.add_page()

    # --- SECTION 3: DATA INTELLIGENCE ---
    title_num = "3." if report_type == "full" else "2."
    if pdf.get_y() > 200: pdf.add_page()
    
    pdf.section_title(f"{title_num} Statistical Recon")
    
    stats = df.describe()
    pdf.create_table(stats)
    pdf.ln(10)

    # --- SECTION 4: VISUAL SURVEILLANCE ---
    if dashboard_imgs:
        title_num = "4." if report_type == "full" else "3."
        if pdf.get_y() > 180: pdf.add_page()
            
        pdf.section_title(f"{title_num} Visual Surveillance")
        
        for i, img_path in enumerate(dashboard_imgs):
            if os.path.exists(img_path):
                if pdf.get_y() > 180: pdf.add_page()
                    
                pdf.set_font("Arial", 'I', 9)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 8, f"Fig {i+1}: Generated Visualization", 0, 1)
                
                pdf.image(img_path, x=10, w=190) 
                pdf.ln(10)
                
    return pdf.output(dest='S').encode('latin-1')

# --- THEME CSS (LORA + MULISH) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,500;0,700;1,400&family=Mulish:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Mulish', sans-serif;
        background-color: #FDFBF7; 
        color: #2C2C2C; 
    }
    
    .stApp {
        background-color: #FDFBF7;
        background-image: none; 
    }

    h1, h2, h3 {
        color: #1C1C1C !important;
        font-family: 'Lora', serif;
        border-bottom: none;
        padding-bottom: 5px;
        font-weight: 700;
        letter-spacing: 0px;
    }
    
    .metric-label {
        color: #666 !important;
        font-family: 'Mulish', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 11px;
    }
    
    .main-title {
        color: #1C1C1C !important; 
        font-family: 'Lora', serif;
        font-weight: 700;
        font-size: 4.5rem; 
        text-align: left;
        width: 100%;
        display: block;
        padding-bottom: 20px;
        border-bottom: 3px solid #800000;
        margin-bottom: 30px;
        text-transform: uppercase; 
    }

    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #EAEAEA; 
        border-left: 6px solid #800000;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        text-align: center;
        transition: all 0.3s ease;
        margin-bottom: 15px;
        border-radius: 20px;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12); 
    }
    .metric-value { 
        color: #800000;
        font-family: 'Lora', serif;
        font-size: 38px;
        font-weight: 700; 
    }

    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF; 
        border: 1px solid #E0E0E0;
        font-family: 'Mulish', sans-serif;
        border-radius: 12px;
        padding: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stDataFrame"] > div {
        background-color: #FFFFFF;
    }

    .stButton>button {
        background-color: #2C2C2C;
        color: #FFF;
        border: none;
        border-radius: 25px; 
        font-family: 'Mulish', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        padding: 12px 30px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { 
        background-color: #800000;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(128,0,0,0.3);
    }
    
    input[type="text"] {
        background: #FFFFFF !important;
        color: #1C1C1C !important;
        border: 1px solid #CCC !important;
        border-radius: 12px;
        padding-left: 15px;
        font-family: 'Mulish', sans-serif;
    }
    
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #FDFBF7; 
        padding: 5px; 
    }
    .stTabs [data-baseweb="tab"] { 
        color: #555; 
        font-family: 'Mulish', sans-serif; 
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #FDFBF7; 
        color: #800000; 
        border-bottom: 3px solid #800000;
    }

    @media only screen and (max-width: 768px) {
        .main-title { font-size: 2.5rem !important; }
        .metric-value { font-size: 28px !important; }
        .stButton>button { width: 100% !important; margin-top: 10px; }
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM MENU")
    uploaded_file = st.file_uploader("UPLOAD DATASET", type=["csv", "xlsx"])
    st.markdown("---")
    
    if DEMO_MODE:
        st.code("STATUS: OFFLINE MODE")
        st.error(f"Error: {debug_error}")
    else:
        st.success("STATUS: ONLINE")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    st.caption("INSIGHTGEN | ANALYTICS SUITE V1.7")

# --- MAIN CONTENT ---
st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)

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
        st.subheader("DATASET OVERVIEW")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[0]}</div><div class="metric-label">TOTAL ROWS</div></div>""", unsafe_allow_html=True)
        with mc2: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[1]}</div><div class="metric-label">COLUMNS</div></div>""", unsafe_allow_html=True)
        with mc3: 
            missing = df.isnull().sum().sum(); color = "#800000" if missing > 0 else "#2E7D32"
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: {color}">{missing}</div><div class="metric-label">MISSING VALUES</div></div>""", unsafe_allow_html=True)
        with mc4: 
            dupes = df.duplicated().sum()
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">DUPLICATES</div></div>""", unsafe_allow_html=True)
        st.write("")

        tab1, tab2 = st.tabs(["AI ANALYSIS", "VISUAL DASHBOARD"])

        # --- TAB 1 ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ANALYSIS QUERY:", placeholder="Ask a question about your data...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("RUN ANALYSIS", use_container_width=True)

            if run_btn and query:
                st.session_state.last_query = query
                
                # --- OPTIMIZED LOADING SEQUENCE ---
                status_container = st.empty()
                
                with status_container.container():
                    # 1. Animation (Looping)
                    st.components.v1.html("""
                    <script src="https://unpkg.com/@dotlottie/player-component@latest/dist/dotlottie-player.mjs" type="module"></script>
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                        <dotlottie-player src="https://lottie.host/0e9443fb-5443-43a1-939b-7b53756db004/WvBcP4Z7Af.lottie" background="transparent" speed="1" style="width: 300px; height: 300px;" loop autoplay></dotlottie-player>
                    </div>
                    """, height=300)
                    
                    # 2. Text Placeholders (Slower Pace)
                    text_placeholder = st.empty()
                    
                    text_placeholder.markdown(f"<h3 style='text-align: center; color: #800000; font-family: Mulish;'>- Reading Dataset...</h3>", unsafe_allow_html=True)
                    time.sleep(2) # SLOWED DOWN TO 2s
                    
                    text_placeholder.markdown(f"<h3 style='text-align: center; color: #800000; font-family: Mulish;'>- Initializing AI Agents...</h3>", unsafe_allow_html=True)
                    time.sleep(2) # SLOWED DOWN TO 2s

                    # 3. Persistent Message (Emoji-Free)
                    text_placeholder.markdown(
                        f"""<h3 style='text-align: center; color: #800000; font-family: Mulish;'>
                        Deep Analysis in Progress...<br>
                        <span style='font-size: 0.7em; color: #666;'>This may take up to 60 seconds. Please wait.</span>
                        </h3>""", 
                        unsafe_allow_html=True
                    )
                
                # -------------------------------

                try:
                    if DEMO_MODE:
                        time.sleep(3) 
                        status_container.empty()
                        st.session_state.analysis_result = f"Query: {query}\nStatus: SIMULATED RESPONSE\nReason: {debug_error}\n1. Trend Detected: Positive.\n2. Correlation: Strong (0.85)."
                        st.session_state.analysis_plot = "simulated"
                    else:
                        if os.path.exists("plot.png"): os.remove("plot.png")
                        
                        from crewai import Crew, Task, Process
                        
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
                        
                        # --- BLOCKING CALL (APP FREEZES HERE FOR ~60s) ---
                        result = crew.kickoff() 
                        # -------------------------------------------------
                        
                        # FORCE CLEAR LOADING SCREEN
                        status_container.empty()
                        
                        st.session_state.analysis_result = str(result)
                        st.session_state.analysis_plot = "plot.png" if os.path.exists("plot.png") else None
                except Exception as e:
                    status_container.empty()
                    st.error(f"RUNTIME ERROR: {e}")

            if st.session_state.analysis_result:
                st.markdown("---")
                st.caption(f"QUERY LOG: {st.session_state.last_query}")
                r1, r2 = st.columns([1.5, 1])
                with r1:
                    st.markdown("### ANALYSIS RESULTS")
                    st.markdown(st.session_state.analysis_result)
                with r2:
                    st.markdown("### CHART PREVIEW")
                    if st.session_state.analysis_plot == "simulated":
                        st.info("Simulated Plot")
                    elif st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png"):
                        st.image("plot.png")
                    else:
                        st.caption("NO VISUALIZATION GENERATED")

        # --- TAB 2 ---
        with tab2:
            st.write("")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1: selected_cat = st.selectbox("FILTER COLUMN", cat_cols)
                with col_f2: unique_vals = df[selected_cat].unique(); selected_val = st.multiselect(f"FILTER VALUES", unique_vals, default=unique_vals[:5])
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df

            dashboard_images = []
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            if not numeric_df.empty:
                # PAPER THEME PLOTS
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Reds', template="plotly_white")
                fig_corr.update_layout(paper_bgcolor="#FDFBF7", plot_bgcolor="#FDFBF7", font_family="Mulish", font_color="#1C1C1C")
                try:
                    fig_corr.write_image("dash_corr.png")
                    dashboard_images.append("dash_corr.png")
                except: pass
                
                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_white")
                fig1.update_traces(marker_color='#800000', marker_line_color='#FFF')
                fig1.update_layout(paper_bgcolor="#FDFBF7", plot_bgcolor="#FDFBF7", font_family="Mulish", font_color="#1C1C1C")
                try:
                    fig1.write_image("dash_hist.png")
                    dashboard_images.append("dash_hist.png")
                except: pass

                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_white")
                fig2.update_traces(marker_color='#1C1C1C')
                fig2.update_layout(paper_bgcolor="#FDFBF7", plot_bgcolor="#FDFBF7", font_family="Mulish", font_color="#1C1C1C")
                try:
                    fig2.write_image("dash_scatter.png")
                    dashboard_images.append("dash_scatter.png")
                except: pass

            d_col1, d_col2 = st.columns([4, 1])
            with d_col1: st.markdown(f"**FILTERED RECORDS:** {len(filtered_df)}") 
            with d_col2:
                try:
                    dash_pdf = generate_pdf("dashboard", df, dashboard_imgs=dashboard_images)
                    st.download_button(label="[ EXPORT PDF ]", data=dash_pdf, file_name="InsightGen_Dashboard_Report.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"PDF Gen Error: {e}")

            st.markdown("---")
            column_config = {}
            for col in filtered_df.select_dtypes(include="number").columns:
                column_config[col] = st.column_config.NumberColumn(col, format="%.2f")
            st.dataframe(filtered_df.head(100), width="stretch", height=300, column_config=column_config)
            
            st.markdown("---")
            if not numeric_df.empty:
                st.markdown("### VISUALIZATION DASHBOARD")
                
                st.plotly_chart(fig_corr, width="stretch")
                gc1, gc2 = st.columns(2)
                with gc1: st.plotly_chart(fig1, width="stretch")
                with gc2: st.plotly_chart(fig2, width="stretch")
            else:
                st.info("NO NUMERIC DATA AVAILABLE")

        with full_report_container:
            if st.session_state.analysis_result:
                plot_to_use = "plot.png" if st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png") else None
                try:
                    full_pdf = generate_pdf("full", df, st.session_state.last_query, str(st.session_state.analysis_result), plot_to_use, dashboard_images)
                    st.download_button(label="[ EXPORT FULL REPORT ]", data=full_pdf, file_name="InsightGen_Full_Analytics_Report.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"Full PDF Error: {e}")

    except Exception as e:
        st.error(f"SYSTEM ERROR: {e}")
else:
    with st.container():
        st.info("READY: UPLOAD DATASET TO BEGIN...")

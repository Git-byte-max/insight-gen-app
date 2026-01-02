# --- 1. SQLITE FIX FOR STREAMLIT CLOUD ---
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
from datetime import datetime
from fpdf import FPDF

# --- 2. CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

st.set_page_config(
    page_title="InsightGen: Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend
try:
    from agents import planner, coder, reporter, DEMO_MODE, debug_error
    import tools
except Exception as e:
    DEMO_MODE = True
    tools = None
    planner = coder = reporter = None
    debug_error = f"System Error: {e}"

# --- 3. SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_plot" not in st.session_state:
    st.session_state.analysis_plot = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- 4. ADVANCED PDF ENGINE (SMART PAGE BREAKS) ---
class PDFReport(FPDF):
    def header(self):
        # Black Background for Header
        self.set_fill_color(10, 10, 10) 
        self.rect(0, 0, 210, 25, 'F')
        
        # Crimson Text
        self.set_font('Arial', 'B', 16)
        self.set_text_color(211, 47, 47) # Crimson
        self.cell(0, 10, 'INSIGHTGEN | ANALYTICS DOSSIER', 0, 1, 'C')
        
        # Subtitle
        self.set_font('Arial', 'I', 10)
        self.set_text_color(200, 200, 200) # Light Grey
        self.cell(0, 0, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'CONFIDENTIAL // Page {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(211, 47, 47) # Crimson
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        # Red Underline
        self.set_draw_color(211, 47, 47)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def body_text(self, text):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0) # Black Text
        self.multi_cell(0, 6, text)
        self.ln(5)

def generate_pdf(report_type, df, query=None, ai_text=None, plot_path=None, dashboard_imgs=None):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- SECTION 1: MISSION OVERVIEW (METRICS) ---
    pdf.section_title("1. Mission Overview")
    
    rows = df.shape[0]
    cols = df.shape[1]
    missing = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    
    pdf.set_font("Courier", 'B', 11)
    pdf.set_fill_color(240, 240, 240) # Light Grey Box
    pdf.cell(90, 10, f" TOTAL RECORDS: {rows}", 1, 0, 'L', 1)
    pdf.cell(90, 10, f" VARIABLES:     {cols}", 1, 1, 'L', 1)
    pdf.cell(90, 10, f" MISSING DATA:  {missing}", 1, 0, 'L', 1)
    pdf.cell(90, 10, f" DUPLICATES:    {dupes}", 1, 1, 'L', 1)
    pdf.ln(10)

    # --- SECTION 2: EXECUTIVE SUMMARY (Full Report Only) ---
    if report_type == "full":
        pdf.section_title("2. Intelligence Report")
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"QUERY SCOPE: {query}", 0, 1)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 11)
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(10)
        
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=190)
            pdf.ln(10)
        pdf.add_page()

    # --- SECTION 3: DATA INTELLIGENCE (STATS) ---
    title_num = "3." if report_type == "full" else "2."
    
    # Check space for table, if low space, move to next page
    if pdf.get_y() > 220:
        pdf.add_page()
        
    pdf.section_title(f"{title_num} Statistical Recon")
    
    pdf.set_font("Courier", size=8)
    stats = df.describe()
    stats_str = stats.to_string()
    
    pdf.set_fill_color(250, 250, 250)
    pdf.multi_cell(0, 5, stats_str, border=1, fill=True)
    pdf.ln(10)

    # --- SECTION 4: VISUAL SURVEILLANCE (CHARTS) ---
    if dashboard_imgs:
        title_num = "4." if report_type == "full" else "3."
        
        # [FIX] Check for orphaned header: If we are near the bottom (>200mm), start new page
        if pdf.get_y() > 200:
            pdf.add_page()
            
        pdf.section_title(f"{title_num} Visual Surveillance")
        
        for i, img_path in enumerate(dashboard_imgs):
            if os.path.exists(img_path):
                # Ensure image doesn't get cut off
                if pdf.get_y() > 200: 
                    pdf.add_page()
                    
                pdf.set_font("Arial", 'I', 9)
                pdf.cell(0, 10, f"Figure {i+1}: Automated Visualization", 0, 1)
                pdf.image(img_path, x=10, w=190) 
                pdf.ln(10)
                
    return pdf.output(dest='S').encode('latin-1')

# --- 5. MOBILE-OPTIMIZED CRIMSON THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;500;900&display=swap');
    
    /* === GLOBAL STYLES === */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #E0E0E0;
        background-color: #0a0a0a; /* Deep Matte Black */
    }
    
    .stApp {
        background-color: #0a0a0a;
        background-image: none; 
    }

    /* === SCROLLBARS === */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #D32F2F; border-radius: 4px; }

    /* === TYPOGRAPHY === */
    h1, h2, h3, .metric-label {
        color: #FF5252 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .main-title {
        color: #D32F2F !important;
        font-weight: 900;
        font-size: 4.5rem; 
        letter-spacing: -2px;
        text-shadow: 2px 2px 0px #333;
        line-height: 1.1;
        text-align: left;
        width: 100%;
        display: block;
    }

    /* === 🔴 METRIC CARDS (FULL RED BORDER) === */
    .metric-card {
        background-color: #161616;
        border: 2px solid #D32F2F; /* FULL RED BORDER */
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(211, 47, 47, 0.1);
        text-align: center;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: pointer;
        margin-bottom: 15px; 
    }
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 0 25px rgba(211, 47, 47, 0.6); 
        background-color: #200505;
        border-color: #FF5252;
    }
    .metric-value { 
        color: #FFF; 
        font-size: 38px;
        font-weight: 900; 
    }
    .metric-label { 
        color: #AAA !important; 
        font-size: 12px; 
        font-weight: bold;
    }

    /* === 🟦 TABLE STYLING (CUSTOM HEADER LOOK) === */
    div[data-testid="stDataFrame"] {
        background-color: #050505; 
        border: 1px solid #333;
        border-top: 5px solid #D32F2F; 
        border-radius: 10px;
        padding: 5px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    }
    
    div[data-testid="stDataFrame"] > div {
        background-color: #050505;
    }

    /* === COMPONENTS (ROUNDED) === */
    .stButton>button {
        background-color: #D32F2F;
        color: white;
        border-radius: 20px; 
        border: none;
        font-weight: 900;
        text-transform: uppercase;
        padding: 10px 20px;
        transition: all 0.2s ease;
        width: auto; 
    }
    .stButton>button:hover { 
        background-color: #B71C1C; 
        transform: translateY(-2px);
        box-shadow: 0 0 15px rgba(211, 47, 47, 0.5);
    }
    
    input[type="text"] {
        background: #111 !important;
        color: #FFF !important;
        border: 1px solid #444 !important;
        border-left: 3px solid #D32F2F !important;
        border-radius: 20px;
        padding-left: 15px;
    }
    
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #000; 
        padding: 8px; 
        border-radius: 20px;
        border: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] { color: #666; font-weight: 700; text-transform: uppercase; }
    .stTabs [aria-selected="true"] { 
        background-color: #D32F2F; 
        color: #FFF; 
        border-radius: 15px;
    }

    /* ================================= */
    /* === 📱 MOBILE RESPONSIVENESS === */
    /* ================================= */
    
    @media only screen and (max-width: 768px) {
        .main-title {
            font-size: 2.8rem !important;
            text-align: left;
        }
        .metric-value { font-size: 28px !important; }
        .metric-card { padding: 15px !important; margin-bottom: 10px !important; }
        .stButton>button { width: 100% !important; margin-top: 10px; }
        .metric-card:hover { transform: none !important; }
        iframe { height: 150px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### > SYSTEM CONFIGURATION")
    uploaded_file = st.file_uploader("UPLOAD DATASET", type=["csv", "xlsx"])
    st.markdown("---")
    
    if DEMO_MODE:
        st.code("STATUS: OFFLINE MODE")
        st.error(f"Error: {debug_error}")
    else:
        st.code("STATUS: SYSTEM ACTIVE")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    st.caption("INSIGHTGEN | ANALYTICS V3.6")

# --- 7. MAIN CONTENT ---
st.markdown("<div class='main-title'>InsightGen</div>", unsafe_allow_html=True)
st.markdown("#### *// ADVANCED DATA ANALYTICS*")

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
            missing = df.isnull().sum().sum(); color = "#D32F2F" if missing > 0 else "#4CAF50"
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: {color}">{missing}</div><div class="metric-label">MISSING VALUES</div></div>""", unsafe_allow_html=True)
        with mc4: 
            dupes = df.duplicated().sum()
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">DUPLICATES</div></div>""", unsafe_allow_html=True)
        st.write("")

        tab1, tab2 = st.tabs(["ANALYSIS INPUT", "VISUALIZATION DASHBOARD"])

        # --- TAB 1 ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ANALYSIS QUERY:", placeholder="> Enter query here...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("RUN ANALYSIS", use_container_width=True)

            if run_btn and query:
                st.session_state.last_query = query
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe("https://lottie.host/embed/4f0b35e7-c2d8-4026-a494-11d54fa5e4f2/edm0jSn651.lottie", height=200, scrolling=False)
                        st.markdown("<center style='color: #D32F2F; font-family: Roboto;'>PROCESSING DATA...</center>", unsafe_allow_html=True)

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
                # CRIMSON THEME PLOTS
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Reds', template="plotly_dark")
                fig_corr.update_layout(paper_bgcolor="#1E1E1E", plot_bgcolor="#1E1E1E", font_color="#FFF")
                try:
                    # Export dark bg image for PDF
                    fig_corr.update_layout(paper_bgcolor="#111")
                    fig_corr.write_image("dash_corr.png")
                    dashboard_images.append("dash_corr.png")
                except: pass
                
                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_dark")
                fig1.update_traces(marker_color='#D32F2F', marker_line_color='#FFF')
                fig1.update_layout(paper_bgcolor="#1E1E1E", plot_bgcolor="#1E1E1E", font_color="#FFF")
                try:
                    fig1.update_layout(paper_bgcolor="#111")
                    fig1.write_image("dash_hist.png")
                    dashboard_images.append("dash_hist.png")
                except: pass

                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_dark")
                fig2.update_traces(marker_color='#FFF')
                fig2.update_layout(paper_bgcolor="#1E1E1E", plot_bgcolor="#1E1E1E", font_color="#FFF")
                try:
                    fig2.update_layout(paper_bgcolor="#111")
                    fig2.write_image("dash_scatter.png")
                    dashboard_images.append("dash_scatter.png")
                except: pass

            d_col1, d_col2 = st.columns([4, 1])
            with d_col1: st.markdown(f"**FILTERED RECORDS:** {len(filtered_df)}") 
            with d_col2:
                try:
                    # Pass 'df' to PDF engine for full stats
                    stats_summary = df.describe()
                    dash_pdf = generate_pdf("dashboard", df, dashboard_imgs=dashboard_images)
                    st.download_button(label="[ EXPORT DASHBOARD PDF ]", data=dash_pdf, file_name="InsightGen_Dashboard_Report.pdf", mime="application/pdf", width="stretch")
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
                # Reset layout for UI
                fig_corr.update_layout(paper_bgcolor="#1E1E1E")
                fig1.update_layout(paper_bgcolor="#1E1E1E")
                fig2.update_layout(paper_bgcolor="#1E1E1E")
                
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

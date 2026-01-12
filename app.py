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
    page_title="InsightGen: Platinum Analytics",
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

# --- 4. ADVANCED PDF ENGINE (PLATINUM THEME) ---
class PDFReport(FPDF):
    def header(self):
        # INDIGO HEADER BAR
        self.set_fill_color(92, 107, 192) # Indigo 400
        self.rect(0, 0, 210, 30, 'F')
        
        # WHITE TITLE
        self.set_font('Arial', 'B', 18)
        self.set_text_color(255, 255, 255) 
        self.set_y(10)
        self.cell(0, 10, 'INSIGHTGEN | ANALYTICS REPORT', 0, 1, 'C')
        
        # SUBTITLE
        self.set_font('Arial', '', 9)
        self.set_text_color(230, 230, 250) # Light Lavender
        self.cell(0, 0, f'GENERATED: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'CONFIDENTIAL // Page {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(44, 62, 80) # Dark Slate Blue
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        # Indigo Underline
        self.set_draw_color(92, 107, 192)
        self.set_line_width(1)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def create_table(self, df):
        """ Renders a Pandas DataFrame as a proper PDF Table """
        self.set_font("Arial", "B", 8)
        self.set_fill_color(240, 242, 245) # Very light grey
        self.set_text_color(0, 0, 0)
        self.set_draw_color(200, 200, 200)
        
        # Headers
        col_width = 190 / (len(df.columns) + 1)
        self.cell(col_width, 8, "Metric", 1, 0, 'C', 1)
        for col in df.columns:
            self.cell(col_width, 8, str(col)[:10], 1, 0, 'C', 1)
        self.ln()
        
        # Data Rows
        self.set_font("Arial", "", 8)
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
    
    # --- SECTION 1: MISSION OVERVIEW (GRID) ---
    pdf.section_title("1. Mission Overview")
    
    rows = df.shape[0]
    cols = df.shape[1]
    missing = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    
    # 2x2 Data Grid
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(92, 107, 192) # Indigo Borders
    
    # Row 1
    pdf.cell(95, 12, f" TOTAL RECORDS: {rows}", 1, 0, 'L', 1)
    pdf.cell(95, 12, f" VARIABLES:     {cols}", 1, 1, 'L', 1)
    # Row 2
    pdf.cell(95, 12, f" MISSING DATA:  {missing}", 1, 0, 'L', 1)
    pdf.cell(95, 12, f" DUPLICATES:    {dupes}", 1, 1, 'L', 1)
    pdf.ln(10)

    # --- SECTION 2: EXECUTIVE SUMMARY (Full Report Only) ---
    if report_type == "full":
        pdf.section_title("2. Intelligence Report")
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"QUERY SCOPE: {query}", 0, 1)
        
        pdf.set_font("Arial", '', 10)
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(10)
        
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=190)
            pdf.ln(10)
        pdf.add_page()

    # --- SECTION 3: DATA INTELLIGENCE (REAL TABLE) ---
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
                    
                pdf.set_font("Arial", 'B', 9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 8, f"FIGURE {i+1}: GENERATED VISUALIZATION", 0, 1)
                
                pdf.image(img_path, x=10, w=190) 
                pdf.ln(10)
                
    return pdf.output(dest='S').encode('latin-1')

# --- 5. PLATINUM SLATE THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* === GLOBAL STYLES === */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #2C3E50; /* Dark Slate */
        background-color: #F8F9FA; /* Off-White Background */
    }
    
    .stApp {
        background-color: #F8F9FA;
        background-image: none; 
    }

    /* === SCROLLBARS === */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #F1F1F1; }
    ::-webkit-scrollbar-thumb { background: #5C6BC0; border-radius: 4px; }

    /* === TYPOGRAPHY === */
    h1, h2, h3 {
        color: #2C3E50 !important;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .metric-label {
        color: #5C6BC0 !important; /* Indigo */
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .main-title {
        color: #1A237E !important; /* Deep Indigo */
        font-weight: 800;
        font-size: 3.5rem; 
        letter-spacing: -1px;
        line-height: 1.1;
        text-align: left;
        width: 100%;
        display: block;
        padding-bottom: 10px;
    }

    /* === ⬜ PLATINUM CARDS (CLEAN SHADOW) === */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0; 
        border-left: 5px solid #5C6BC0; /* Indigo Left Border */
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: all 0.2s ease;
        margin-bottom: 15px; 
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1); 
    }
    .metric-value { 
        color: #2C3E50; 
        font-size: 32px;
        font-weight: 700; 
    }
    .metric-label { 
        color: #7F8C8D !important; 
        font-size: 11px; 
        font-weight: 600;
    }

    /* === 🟦 TABLE STYLING (CLEAN) === */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF; 
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stDataFrame"] > div {
        background-color: #FFFFFF;
    }

    /* === COMPONENTS (BUTTONS & INPUTS) === */
    .stButton>button {
        background-color: #5C6BC0; /* Indigo */
        color: white;
        border-radius: 6px; 
        border: none;
        font-weight: 600;
        text-transform: uppercase;
        padding: 10px 20px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(92, 107, 192, 0.3);
    }
    .stButton>button:hover { 
        background-color: #3F51B5; 
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(92, 107, 192, 0.4);
    }
    
    input[type="text"] {
        background: #FFFFFF !important;
        color: #333 !important;
        border: 1px solid #D1D1D1 !important;
        border-left: 3px solid #5C6BC0 !important;
        border-radius: 6px;
        padding-left: 15px;
    }
    
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #FFFFFF; 
        padding: 8px; 
        border-radius: 8px;
        border: 1px solid #E0E0E0;
    }
    .stTabs [data-baseweb="tab"] { color: #555; font-weight: 600; }
    .stTabs [aria-selected="true"] { 
        background-color: #5C6BC0; 
        color: #FFF; 
        border-radius: 6px;
    }

    /* ================================= */
    /* === 📱 MOBILE RESPONSIVENESS === */
    /* ================================= */
    
    @media only screen and (max-width: 768px) {
        .main-title {
            font-size: 2.2rem !important;
        }
        .metric-value { font-size: 24px !important; }
        .metric-card { padding: 15px !important; margin-bottom: 10px !important; }
        .stButton>button { width: 100% !important; margin-top: 10px; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR ---
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
    st.caption("INSIGHTGEN | PLATINUM EDITION V2.0")

# --- 7. MAIN CONTENT ---
st.markdown("<div class='main-title'>InsightGen</div>", unsafe_allow_html=True)
st.markdown("#### *// INTELLIGENT ANALYTICS SUITE*")

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
            missing = df.isnull().sum().sum(); color = "#D32F2F" if missing > 0 else "#43A047"
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
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        # Use a simpler/cleaner loader for Platinum theme
                        st.spinner("Processing Data Intelligence...")

                try:
                    if DEMO_MODE:
                        time.sleep(2) 
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
                # PLATINUM THEME PLOTS (Clean White/Blue)
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Blues', template="plotly_white")
                fig_corr.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#333")
                try:
                    fig_corr.write_image("dash_corr.png")
                    dashboard_images.append("dash_corr.png")
                except: pass
                
                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_white")
                fig1.update_traces(marker_color='#5C6BC0', marker_line_color='#FFF')
                fig1.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#333")
                try:
                    fig1.write_image("dash_hist.png")
                    dashboard_images.append("dash_hist.png")
                except: pass

                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_white")
                fig2.update_traces(marker_color='#3F51B5')
                fig2.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#333")
                try:
                    fig2.write_image("dash_scatter.png")
                    dashboard_images.append("dash_scatter.png")
                except: pass

            d_col1, d_col2 = st.columns([4, 1])
            with d_col1: st.markdown(f"**FILTERED RECORDS:** {len(filtered_df)}") 
            with d_col2:
                try:
                    # Pass original DF to ensure accurate summary
                    dash_pdf = generate_pdf("dashboard", df, dashboard_imgs=dashboard_images)
                    st.download_button(label="[ DOWNLOAD PDF ]", data=dash_pdf, file_name="InsightGen_Dashboard_Report.pdf", mime="application/pdf", width="stretch")
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

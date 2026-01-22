import os
import sys

# --- CRITICAL FIX: DISABLE TELEMETRY AT THE ENTRY POINT ---
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
from datetime import datetime, timedelta, timezone
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(
    page_title="INSIGHTGEN: Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend
try:
    import tools
    from agents import planner, coder, reporter, DEMO_MODE, debug_error
except Exception as e:
    st.error(f"Backend Import Error: {e}")
    DEMO_MODE = True
    tools = None
    planner = coder = reporter = None
    debug_error = f"System Error: {e}"

# --- SESSION STATE INITIALIZATION ---
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "analysis_plot" not in st.session_state:
    st.session_state.analysis_plot = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "analysis_time" not in st.session_state:
    st.session_state.analysis_time = None
if "current_df" not in st.session_state:
    st.session_state.current_df = None
if "current_filename" not in st.session_state:
    st.session_state.current_filename = None

# --- HELPER: TIME GREETING (IST) ---
def get_time_greeting():
    # Define IST timezone (UTC + 5:30)
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    # Get current time in IST
    now_ist = datetime.now(ist_offset)
    hour = now_ist.hour
    
    if hour < 12: return "Good Morning"
    elif 12 <= hour < 18: return "Good Afternoon"
    else: return "Good Evening"

# --- HELPER: DATA LOADER ---
def load_data(uploaded_file):
    """Reads file and saves to session state"""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.session_state.current_df = df
        st.session_state.current_filename = uploaded_file.name
        
        if tools: tools.df = df
        df.to_csv("dataset.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return False

# --- ADVANCED PDF ENGINE ---
class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(44, 62, 80) # Dark Slate Blue
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(255, 255, 255) 
        self.set_y(10)
        self.cell(0, 10, 'INSIGHTGEN | ANALYTICS REPORT', 0, 1, 'C')
        self.set_font('Helvetica', '', 10) 
        self.set_text_color(240, 240, 230) 
        self.cell(0, 0, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, f'Confidential // Page {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(44, 62, 80) 
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        self.set_draw_color(44, 62, 80)
        self.set_line_width(1)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def create_table(self, df):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(224, 247, 250) 
        self.set_text_color(0, 0, 0)
        self.set_draw_color(200, 200, 200) 
        col_width = 190 / (len(df.columns) + 1)
        self.cell(col_width, 8, "Metric", 1, 0, 'C', 1)
        for col in df.columns:
            self.cell(col_width, 8, str(col)[:10], 1, 0, 'C', 1)
        self.ln()
        self.set_font("Helvetica", "", 9)
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
    
    pdf.section_title("1. Mission Overview")
    rows = df.shape[0]
    cols = df.shape[1]
    missing = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    
    pdf.set_font("Helvetica", '', 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(200, 200, 200)
    pdf.cell(95, 12, f" Total Records: {rows}", 1, 0, 'L', 1)
    pdf.cell(95, 12, f" Variables: {cols}", 1, 1, 'L', 1)
    pdf.cell(95, 12, f" Missing Data: {missing}", 1, 0, 'L', 1)
    pdf.cell(95, 12, f" Duplicates: {dupes}", 1, 1, 'L', 1)
    pdf.ln(10)

    if report_type == "full":
        pdf.section_title("2. Intelligence Report")
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 8, f"QUERY SCOPE: {query}", 0, 1)
        pdf.set_font("Helvetica", '', 10)
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(10)
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=190)
            pdf.ln(10)
        pdf.add_page()

    title_num = "3." if report_type == "full" else "2."
    if pdf.get_y() > 200: pdf.add_page()
    pdf.section_title(f"{title_num} Statistical Recon")
    stats = df.describe()
    pdf.create_table(stats)
    pdf.ln(10)

    if dashboard_imgs:
        title_num = "4." if report_type == "full" else "3."
        if pdf.get_y() > 180: pdf.add_page()
        pdf.section_title(f"{title_num} Visual Surveillance")
        for i, img_path in enumerate(dashboard_imgs):
            if os.path.exists(img_path):
                if pdf.get_y() > 180: pdf.add_page()
                pdf.set_font("Helvetica", 'I', 9)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 8, f"Fig {i+1}: Generated Visualization", 0, 1)
                pdf.image(img_path, x=10, w=190) 
                pdf.ln(10)
                
    return pdf.output(dest='S').encode('latin-1')

# --- THEME CSS (GLASSMORPHISM + HOVER) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@600;800&family=Mulish:wght@300;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Mulish', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2C3E50;
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    h1, h2, h3 {
        color: #2C3E50 !important;
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
    }
    
    .main-title {
        color: #2C3E50 !important; 
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 3.5rem; 
        text-transform: uppercase; 
    }
    
    .greeting-text {
        font-family: 'Mulish', sans-serif;
        font-size: 1.2rem;
        color: #34495E;
        font-weight: 600;
    }

    /* METRIC CARD WITH HOVER EFFECT */
    .metric-card {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        text-align: center;
        border-radius: 15px;
        transition: all 0.3s ease; /* Smooth transition */
    }
    
    .metric-card:hover {
        transform: translateY(-5px); /* Lift up effect */
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.2); /* Enhanced shadow */
        border: 1px solid rgba(255, 255, 255, 0.5);
    }

    .metric-value { 
        color: #2C3E50;
        font-family: 'Manrope', sans-serif;
        font-size: 32px;
        font-weight: 800; 
    }
    .metric-label {
        font-family: 'Mulish', sans-serif;
        font-size: 10px;
        font-weight: 700;
        color: #5D6D7E;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stChatMessage {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    div[data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.4);
        border: 2px dashed #B0BEC5;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .streamlit-expanderHeader {
        font-family: 'Mulish', sans-serif;
        font-size: 0.9rem;
        color: #2C3E50;
        background: rgba(255, 255, 255, 0.4);
        border-radius: 10px;
    }
    
    div[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (DYNAMIC) ---
with st.sidebar:
    st.markdown("### SYSTEM MENU")
    
    # LOGIC: Show uploader here ONLY if data is already loaded
    if st.session_state.current_df is not None:
        st.success(f"Active: {st.session_state.current_filename}")
        
        sidebar_file = st.file_uploader("Change Dataset", type=["csv", "xlsx"], key="sidebar_uploader")
        if sidebar_file:
            if load_data(sidebar_file):
                st.rerun()

        if st.button("Reset Session", use_container_width=True):
            st.session_state.current_df = None
            st.session_state.current_filename = None
            st.session_state.analysis_history = []
            st.session_state.analysis_result = None
            st.rerun()
    else:
        st.info("Waiting for data upload...")

    st.markdown("---")
    
    if DEMO_MODE:
        st.code("STATUS: OFFLINE MODE")
        st.error(f"Error: {debug_error}")
    else:
        st.success("STATUS: ONLINE")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    st.caption("INSIGHTGEN | ANALYTICS SUITE V2.1")

# --- MAIN CONTENT ---

# 1. HEADER
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    greeting = get_time_greeting()
    st.markdown(f"<div class='greeting-text'>{greeting}, Analyst.</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)
with header_col2:
    st.components.v1.html("""
    <script src="https://unpkg.com/@dotlottie/player-component@latest/dist/dotlottie-player.mjs" type="module"></script>
    <dotlottie-player src="https://lottie.host/e519ba57-b007-43c2-a64e-08d2863f458b/agikvzJbA3.lottie" background="transparent" speed="1" style="width: 120px; height: 120px;" loop autoplay></dotlottie-player>
    """, height=140)

st.markdown("---")

# 2. LOGIC CONTROLLER
# IF NO DATA: Show Main Page Uploader
if st.session_state.current_df is None:
    uploaded_file = st.file_uploader(
        "Start Analysis: Drag and drop your dataset here", 
        type=["csv", "xlsx"],
        help="Supported formats: .CSV and .XLSX",
        key="main_uploader"
    )
    
    if uploaded_file:
        # Load Data & Trigger Rerun (This hides main uploader)
        if load_data(uploaded_file):
            st.rerun()
            
    if not uploaded_file:
        st.caption("Upload a dataset to activate the Neural Engine.")

# IF DATA EXISTS: Show Dashboard (Even if main uploader is gone)
else:
    df = st.session_state.current_df
    
    # Ensure Tools has access (in case of fresh rerun)
    if tools: tools.df = df
    df.to_csv("dataset.csv", index=False)

    with st.expander(f"Active Dataset: {st.session_state.current_filename}", expanded=False):
        st.info("To change files, use the sidebar uploader or click 'Reset Session'.")

    # --- DASHBOARD & CHAT UI ---
    st.subheader("DATASET OVERVIEW")
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[0]}</div><div class="metric-label">TOTAL ROWS</div></div>""", unsafe_allow_html=True)
    with mc2: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[1]}</div><div class="metric-label">COLUMNS</div></div>""", unsafe_allow_html=True)
    with mc3: 
        missing = df.isnull().sum().sum(); color = "#C0392B" if missing > 0 else "#27AE60"
        st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: {color}">{missing}</div><div class="metric-label">MISSING VALUES</div></div>""", unsafe_allow_html=True)
    with mc4: 
        dupes = df.duplicated().sum()
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">DUPLICATES</div></div>""", unsafe_allow_html=True)
    st.write("")

    tab1, tab2 = st.tabs(["AI ANALYST", "VISUAL DASHBOARD"])

    with tab1:
        st.write("")
        for message in st.session_state.analysis_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "image" in message and message["image"]:
                    st.image(message["image"])

        query = st.chat_input("Ask a question about your data...")
        
        if query:
            st.session_state.analysis_history.append({"role": "user", "content": query})
            st.session_state.last_query = query
            
            with st.chat_message("user"):
                st.markdown(query)

            with st.chat_message("assistant"):
                status_placeholder = st.empty()
                with status_placeholder.container():
                    st.components.v1.html("""
                    <script src="https://unpkg.com/@dotlottie/player-component@latest/dist/dotlottie-player.mjs" type="module"></script>
                    <div style="display: flex; justify-content: center;">
                        <dotlottie-player src="https://lottie.host/e519ba57-b007-43c2-a64e-08d2863f458b/agikvzJbA3.lottie" background="transparent" speed="1" style="width: 150px; height: 150px;" loop autoplay></dotlottie-player>
                    </div>
                    """, height=160)
                    st.caption("Analyzing data patterns...")

                try:
                    if DEMO_MODE:
                        time.sleep(2) 
                        result_text = f"**Simulated Analysis:**\nQuery: {query}\nCorrelation: 0.85 (Strong)."
                        plot_file = None
                        status_placeholder.empty()
                        st.markdown(result_text)
                    else:
                        if os.path.exists("plot.png"): os.remove("plot.png")
                        
                        start_time = time.time()
                        from crewai import Crew, Task, Process
                        
                        col_list = list(df.columns)
                        data_context = f"Columns: {col_list}. "
                        
                        task_plan = Task(
                            description=f"{data_context} user query: '{query}'. Output 1-sentence plan.", 
                            expected_output="Brief plan", 
                            agent=planner
                        )
                        task_code = Task(
                            description="Write ONE Python script. Check types (Cat/Num). Calc stats. Save 'plot.png'.", 
                            expected_output="Code output", 
                            agent=coder, 
                            context=[task_plan]
                        )
                        task_report = Task(
                            description="Format findings into Markdown (Summary, Stats, Implications).", 
                            expected_output="Markdown Report", 
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
                        end_time = time.time()
                        
                        status_placeholder.empty()
                        
                        result_text = str(result)
                        st.markdown(result_text)
                        
                        plot_file = None
                        if os.path.exists("plot.png"):
                            plot_file = "plot.png"
                            st.image(plot_file)
                            
                        elapsed = round(end_time - start_time, 2)
                        st.caption(f"Analysis completed in {elapsed}s")

                    st.session_state.analysis_history.append({
                        "role": "assistant", 
                        "content": result_text,
                        "image": plot_file
                    })
                    
                    st.session_state.analysis_result = result_text
                    st.session_state.analysis_plot = plot_file

                except Exception as e:
                    status_placeholder.empty()
                    st.error(f"Runtime Error: {e}")

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
            corr = numeric_df.corr()
            fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Blues', template="plotly_white")
            fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_family="Mulish", font_color="#2C3E50")
            try:
                fig_corr.write_image("dash_corr.png")
                dashboard_images.append("dash_corr.png")
            except: pass
            
            x_axis_val = numeric_df.columns[0]
            fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_white")
            fig1.update_traces(marker_color='#3498DB', marker_line_color='#FFF')
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_family="Mulish", font_color="#2C3E50")
            try:
                fig1.write_image("dash_hist.png")
                dashboard_images.append("dash_hist.png")
            except: pass

            y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
            fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_white")
            fig2.update_traces(marker_color='#2C3E50')
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_family="Mulish", font_color="#2C3E50")
            try:
                fig2.write_image("dash_scatter.png")
                dashboard_images.append("dash_scatter.png")
            except: pass

        d_col1, d_col2 = st.columns([4, 1])
        with d_col1: st.markdown(f"**FILTERED RECORDS:** {len(filtered_df)}") 
        with d_col2:
            try:
                dash_pdf = generate_pdf("dashboard", df, dashboard_imgs=dashboard_images)
                st.download_button(label="EXPORT PDF", data=dash_pdf, file_name="InsightGen_Dashboard_Report.pdf", mime="application/pdf", width="stretch")
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
        if st.session_state.analysis_history:
            try:
                last_result = st.session_state.analysis_history[-1]["content"]
                last_img = st.session_state.analysis_history[-1].get("image")
                full_pdf = generate_pdf("full", df, st.session_state.last_query, str(last_result), last_img, dashboard_images)
                st.download_button(label="EXPORT FULL REPORT", data=full_pdf, file_name="InsightGen_Full_Analytics_Report.pdf", mime="application/pdf", width="stretch")
            except Exception as e:
                pass

    if tools: tools.df = df

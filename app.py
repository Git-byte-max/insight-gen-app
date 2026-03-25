import os
import sys
import math
import io

# --- CRITICAL FIX: DISABLE ALL TELEMETRY AT THE ENTRY POINT ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

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
if "current_df" not in st.session_state:
    st.session_state.current_df = None
if "current_filename" not in st.session_state:
    st.session_state.current_filename = None

# --- HELPER: TIME GREETING (IST) ---
def get_time_greeting():
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_offset)
    hour = now_ist.hour
    
    if hour < 12: return "Good Morning"
    elif 12 <= hour < 18: return "Good Afternoon"
    else: return "Good Evening"

# --- SPRINT 6: PERFORMANCE CACHING ---
@st.cache_data(show_spinner=False)
def process_dataframe(file_bytes, filename):
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    else:
        return pd.read_excel(io.BytesIO(file_bytes))

def load_data_to_session(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        df = process_dataframe(file_bytes, uploaded_file.name)
        
        st.session_state.current_df = df
        st.session_state.current_filename = uploaded_file.name
        
        if tools: tools.df = df
        df.to_csv("dataset.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Failed to parse file. Please ensure it is a valid, uncorrupted CSV or Excel document. Error: {e}")
        return False

# --- ADVANCED PDF ENGINE ---
class PDFReport(FPDF):
    def set_filename(self, filename):
        self.filename = filename

    def header(self):
        self.set_fill_color(44, 62, 80) 
        self.rect(0, 0, 210, 35, 'F') # Slightly taller to fit the filename
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(255, 255, 255) 
        self.set_y(10)
        self.cell(0, 8, 'INSIGHTGEN | ANALYTICS REPORT', 0, 1, 'C')
        
        ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        self.set_font('Helvetica', '', 10) 
        self.set_text_color(240, 240, 230) 
        self.cell(0, 6, f'Generated: {ist_now.strftime("%Y-%m-%d %H:%M")} (IST)', 0, 1, 'C')
        
        # SPRINT 6: Added Filename to PDF Header
        fname = getattr(self, 'filename', 'Unknown File')
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(173, 216, 230) # Light blue text for the filename
        self.cell(0, 6, f'Source Data: {fname}', 0, 1, 'C')
        self.ln(20)

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

def generate_pdf(report_type, df, query=None, ai_text=None, plot_path=None, dashboard_imgs=None, filename="Unknown"):
    pdf = PDFReport()
    pdf.set_filename(filename)
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
        if pdf.get_y() > 80: 
            pdf.add_page()
            
        pdf.section_title(f"{title_num} Visual Surveillance")
        
        for i, img_path in enumerate(dashboard_imgs):
            if os.path.exists(img_path):
                if pdf.get_y() > 130: 
                    pdf.add_page()
                
                pdf.set_font("Helvetica", 'I', 9)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 8, f"Fig {i+1}: Generated Visualization", 0, 1)
                pdf.image(img_path, x=10, w=190) 
                pdf.ln(10)
                
    return pdf.output(dest='S').encode('latin-1')

# --- THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@600;800&family=Mulish:wght@300;500&display=swap');
    html, body, [class*="css"] { font-family: 'Mulish', sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: #2C3E50; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    h1, h2, h3 { color: #2C3E50 !important; font-family: 'Manrope', sans-serif; font-weight: 800; }
    .main-title { color: #2C3E50 !important; font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 3.5rem; text-transform: uppercase; }
    .greeting-text { font-family: 'Mulish', sans-serif; font-size: 1.2rem; color: #34495E; font-weight: 600; }
    
    /* Active File Header Styling */
    .file-header { font-family: 'Manrope', sans-serif; font-size: 1.4rem; color: #2C3E50; font-weight: 800; padding: 10px 0px 20px 0px; border-bottom: 2px solid rgba(44, 62, 80, 0.1); margin-bottom: 20px; }
    .file-header span { color: #3498DB; background: rgba(255, 255, 255, 0.6); padding: 4px 12px; border-radius: 6px; font-weight: 600; font-size: 1.2rem; }

    .metric-card { background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3); padding: 20px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1); text-align: center; border-radius: 15px; transition: transform 0.3s ease, box-shadow 0.3s ease; }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.2); }
    .metric-value { color: #2C3E50; font-family: 'Manrope', sans-serif; font-size: 32px; font-weight: 800; }
    .metric-label { font-family: 'Mulish', sans-serif; font-size: 10px; font-weight: 700; color: #5D6D7E; text-transform: uppercase; letter-spacing: 1px; }
    button[data-baseweb="tab"] { transition: all 0.3s ease; border-radius: 8px 8px 0 0; margin: 0 4px; border: none !important; }
    button[data-baseweb="tab"]:hover { background-color: rgba(255, 255, 255, 0.5) !important; transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); color: #2C3E50 !important; }
    .stChatMessage { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(5px); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 15px; padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="stFileUploader"] { background: rgba(255, 255, 255, 0.4); border: 2px dashed #B0BEC5; border-radius: 20px; padding: 30px; text-align: center; backdrop-filter: blur(10px); }
    div[data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.5); backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.3); }
    
    /* SPRINT 6: Custom Styling for Download Buttons */
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-family: 'Manrope', sans-serif;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
        width: 100%;
    }
    div[data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(52, 152, 219, 0.5);
        background: linear-gradient(135deg, #2980B9 0%, #3498DB 100%);
        color: white !important;
        border: none;
    }
    div[data-testid="stDownloadButton"] button p {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM MENU")
    
    if st.session_state.current_df is not None:
        sidebar_file = st.file_uploader("Change Dataset", type=["csv", "xlsx"], key="sidebar_uploader")
        if sidebar_file and load_data_to_session(sidebar_file):
            st.rerun()

        if st.button("Reset Session", use_container_width=True):
            st.session_state.current_df = None
            st.session_state.current_filename = None
            st.session_state.analysis_history = []
            st.session_state.analysis_plot = None
            st.rerun()
    else:
        st.info("Waiting for data upload...")

    st.markdown("---")
    if DEMO_MODE:
        st.error("STATUS: OFFLINE (Missing API Key)")
    else:
        st.success("STATUS: ONLINE")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    st.caption("INSIGHTGEN | ANALYTICS SUITE V2.1")

# --- MAIN CONTENT ---
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown(f"<div class='greeting-text'>{get_time_greeting()}, Analyst.</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)
with header_col2:
    st.components.v1.html("""
    <script src="https://unpkg.com/@dotlottie/player-component@latest/dist/dotlottie-player.mjs" type="module"></script>
    <dotlottie-player src="https://lottie.host/e519ba57-b007-43c2-a64e-08d2863f458b/agikvzJbA3.lottie" background="transparent" speed="1" style="width: 120px; height: 120px;" loop autoplay></dotlottie-player>
    """, height=140)

st.markdown("---")

if st.session_state.current_df is None:
    uploaded_file = st.file_uploader("Start Analysis: Drag and drop your dataset here", type=["csv", "xlsx"], key="main_uploader")
    if uploaded_file and load_data_to_session(uploaded_file):
        st.rerun()

else:
    df = st.session_state.current_df
    if tools: tools.df = df

    # SPRINT 6: Active File Header added directly to the UI
    st.markdown(f"<div class='file-header'>Active Dataset: <span>{st.session_state.current_filename}</span></div>", unsafe_allow_html=True)

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
                    if os.path.exists(message["image"]):
                        with open(message["image"], "rb") as file:
                            st.download_button("Download This Plot", data=file, file_name=f"ai_plot_{int(time.time())}.png", mime="image/png", key=f"dl_{time.time()}")

        query = st.chat_input("Ask a question about your data...")
        
        if query:
            if DEMO_MODE:
                st.error("API Key missing. Cannot process query.")
            else:
                st.session_state.analysis_history.append({"role": "user", "content": query})
                st.session_state.last_query = query
                
                with st.chat_message("user"): st.markdown(query)

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
                        if os.path.exists("plot.png"): os.remove("plot.png")
                        
                        start_time = time.time()
                        from crewai import Crew, Task, Process
                        
                        history_context = ""
                        if len(st.session_state.analysis_history) > 1:
                            recent_history = st.session_state.analysis_history[-5:-1]
                            history_context = "RECENT HISTORY:\n" + "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in recent_history if not msg.get('image')])
                        
                        task_plan = Task(description=f"Columns: {list(df.columns)}. {history_context}\nNEW QUERY: '{query}'. Plan exactly what code to write.", expected_output="Brief plan", agent=planner)
                        task_code = Task(description="Write ONE Python script. Save plots as 'plot.png' with a white background.", expected_output="Code output", agent=coder, context=[task_plan])
                        task_report = Task(description="Format findings into Markdown.", expected_output="Markdown Report", agent=reporter, context=[task_code])
                        
                        crew = Crew(agents=[planner, coder, reporter], tasks=[task_plan, task_code, task_report], process=Process.sequential, verbose=True)
                        result_text = str(crew.kickoff()) 
                        
                        status_placeholder.empty()
                        st.markdown(result_text)
                        
                        plot_file = "plot.png" if os.path.exists("plot.png") else None
                        if plot_file:
                            st.image(plot_file)
                            with open(plot_file, "rb") as file:
                                st.download_button("Download Analysis Plot", data=file, file_name="ai_analysis_plot.png", mime="image/png")
                                
                        st.caption(f"Analysis completed in {round(time.time() - start_time, 2)}s")

                        st.session_state.analysis_history.append({"role": "assistant", "content": result_text, "image": plot_file})
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
            num_cols_list = numeric_df.columns.tolist()
            st.markdown("### VISUALIZATION DASHBOARD")
            
            d_ax1, d_ax2 = st.columns(2)
            with d_ax1: x_axis_val = st.selectbox("Select X-Axis", num_cols_list, index=0)
            with d_ax2: y_axis_val = st.selectbox("Select Y-Axis", num_cols_list, index=1 if len(num_cols_list) > 1 else 0)
            
            # Generating Charts with Solid Backgrounds for Export
            fig_corr = px.imshow(numeric_df.corr(), text_auto=True, aspect="auto", color_continuous_scale='Blues', template="plotly_white")
            fig_corr.update_layout(font_family="Mulish", font_color="#2C3E50", paper_bgcolor="white", plot_bgcolor="white")
            try: fig_corr.write_image("dash_corr.png"); dashboard_images.append("dash_corr.png")
            except: pass
            fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)") # Revert for UI
            
            fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_white")
            fig1.update_traces(marker_color='#3498DB', marker_line_color='#FFF')
            fig1.update_layout(font_family="Mulish", font_color="#2C3E50", paper_bgcolor="white", plot_bgcolor="white")
            try: fig1.write_image("dash_hist.png"); dashboard_images.append("dash_hist.png")
            except: pass
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)") # Revert for UI

            fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_white")
            fig2.update_traces(marker_color='#2C3E50')
            fig2.update_layout(font_family="Mulish", font_color="#2C3E50", paper_bgcolor="white", plot_bgcolor="white")
            try: fig2.write_image("dash_scatter.png"); dashboard_images.append("dash_scatter.png")
            except: pass
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)") # Revert for UI

            # Render Charts with Clean Download Buttons
            st.plotly_chart(fig_corr, width="stretch")
            if os.path.exists("dash_corr.png"):
                with open("dash_corr.png", "rb") as f: st.download_button("Download Correlation Matrix", f, "correlation_matrix.png", "image/png")
            
            gc1, gc2 = st.columns(2)
            with gc1: 
                st.plotly_chart(fig1, width="stretch")
                if os.path.exists("dash_hist.png"):
                    with open("dash_hist.png", "rb") as f: st.download_button("Download Histogram", f, "histogram.png", "image/png")
            with gc2: 
                st.plotly_chart(fig2, width="stretch")
                if os.path.exists("dash_scatter.png"):
                    with open("dash_scatter.png", "rb") as f: st.download_button("Download Scatter Plot", f, "scatter_plot.png", "image/png")

        d_col1, d_col2 = st.columns([4, 1])
        with d_col1: st.markdown(f"**FILTERED RECORDS:** {len(filtered_df)}") 
        with d_col2:
            try:
                dash_pdf = generate_pdf("dashboard", df, dashboard_imgs=dashboard_images, filename=st.session_state.current_filename)
                st.download_button(label="EXPORT PDF DASHBOARD", data=dash_pdf, file_name=f"Dashboard_{st.session_state.current_filename}.pdf", mime="application/pdf", width="stretch")
            except Exception as e:
                pass

        st.markdown("---")
        column_config = {}
        for col in filtered_df.select_dtypes(include="number").columns:
            clean_col = filtered_df[col].replace([float('inf'), float('-inf')], float('nan')).dropna()
            if not clean_col.empty:
                min_val, max_val = float(clean_col.min()), float(clean_col.max())
                if math.isfinite(min_val) and math.isfinite(max_val) and (max_val > min_val):
                    column_config[col] = st.column_config.ProgressColumn(col, help=f"Range: {min_val:.2f} to {max_val:.2f}", format="%.2f", min_value=min_val, max_value=max_val)
        
        st.dataframe(filtered_df.head(100), width="stretch", height=300, column_config=column_config)
        
        if numeric_df.empty: st.info("NO NUMERIC DATA AVAILABLE")

    with full_report_container:
        if st.session_state.analysis_history:
            try:
                last_result = st.session_state.analysis_history[-1]["content"]
                last_img = st.session_state.analysis_history[-1].get("image")
                full_pdf = generate_pdf("full", df, st.session_state.last_query, str(last_result), last_img, dashboard_images, filename=st.session_state.current_filename)
                st.download_button(label="EXPORT FULL INTELLIGENCE REPORT", data=full_pdf, file_name=f"Full_Report_{st.session_state.current_filename}.pdf", mime="application/pdf", width="stretch")
            except Exception as e:
                pass

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
    page_title="InsightGen: Lab",
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
        # BRANDING: Professional
        self.cell(0, 10, 'InsightGen: Research Report', 0, 1, 'C')
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
        pdf.cell(0, 10, "1. Executive Summary", 0, 1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"Research Question: {query}", 0, 1)
        pdf.set_font("Arial", size=10)
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(5)
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=170)
        pdf.add_page()

    pdf.set_font("Arial", 'B', 14)
    title = "2. Statistical Overview" if report_type == "full" else "Statistical Report"
    pdf.cell(0, 10, title, 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Data Description:", 0, 1)
    pdf.set_font("Courier", size=8)
    stats_str = df_stats.to_string()
    pdf.multi_cell(0, 5, stats_str)
    pdf.ln(10)

    if dashboard_imgs:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Visual Evidence:", 0, 1)
        pdf.ln(5)
        for img_path in dashboard_imgs:
            if os.path.exists(img_path):
                pdf.image(img_path, x=10, w=180)
                pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. LABORATORY THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* GLOBAL STYLES */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F2937; /* Dark Gray */
        background-color: #F9FAFB; /* Light Gray/White */
        font-size: 16px;
    }
    
    /* CLEAN GRID BACKGROUND */
    .stApp {
        background-color: #FFFFFF;
        background-image: radial-gradient(#E5E7EB 1px, transparent 1px);
        background-size: 24px 24px;
    }

    /* SCROLLBARS */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #F3F4F6; }
    ::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 4px; }
    
    /* HEADERS */
    .main-title {
        font-family: 'Inter', sans-serif;
        color: #111827;
        font-size: 4rem;
        font-weight: 800;
        letter-spacing: -2px;
        line-height: 1;
    }
    h1, h2, h3 { 
        font-family: 'Inter', sans-serif !important; 
        color: #111827 !important; 
        font-weight: 700 !important;
    }

    /* METRIC CARDS (Clinical Style) */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: all 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: #2563EB; }
    
    .metric-value { 
        font-family: 'Inter', sans-serif; 
        font-size: 38px; 
        color: #2563EB; /* Royal Blue */
        font-weight: 700;
    }
    .metric-label { 
        font-size: 12px; 
        color: #6B7280; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        font-weight: 600;
        margin-top: 5px;
    }

    /* BUTTONS (Clean Tech) */
    .stButton>button {
        background-color: #2563EB;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        border: none;
        border-radius: 8px; 
        font-weight: 600;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover { 
        background-color: #1D4ED8; 
        color: #FFFFFF; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 2px solid #E5E7EB; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: transparent; 
        border: none; 
        color: #6B7280; 
        font-family: 'Inter', sans-serif; 
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { 
        background-color: transparent; 
        color: #2563EB; 
        border-bottom: 2px solid #2563EB;
    }
    
    /* DATAFRAME & INPUTS */
    div[data-testid="stDataFrame"] { border: 1px solid #E5E7EB; border-radius: 8px; }
    input[type="text"] { 
        background-color: #FFFFFF !important; 
        color: #1F2937 !important; 
        border: 1px solid #D1D5DB !important; 
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### > CONFIGURATION")
    uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx"])
    st.markdown("---")
    
    # 🟢 DEBUGGER
    if DEMO_MODE:
        st.code("STATUS: OFFLINE (SIM)")
        st.error(f"Reason: {debug_error}")
        if "API Key Missing" in str(debug_error):
            st.warning("Please check Secrets settings.")
    else:
        st.success("STATUS: ONLINE (SECURE)")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    st.caption("INSIGHTGEN | LAB VERSION 2.0")

# --- 7. MAIN CONTENT ---
st.markdown("<div class='main-title'>InsightGen</div>", unsafe_allow_html=True)
st.markdown("#### *Analysis & Research Environment*")

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
        st.subheader("Dataset Health Check")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[0]}</div><div class="metric-label">Total Rows</div></div>""", unsafe_allow_html=True)
        with mc2: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[1]}</div><div class="metric-label">Variables</div></div>""", unsafe_allow_html=True)
        with mc3: 
            missing = df.isnull().sum().sum(); color = "#EF4444" if missing > 0 else "#2563EB" # Red vs Blue
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: {color}">{missing}</div><div class="metric-label">Missing Values</div></div>""", unsafe_allow_html=True)
        with mc4: 
            dupes = df.duplicated().sum()
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">Duplicates</div></div>""", unsafe_allow_html=True)
        st.write("")

        tab1, tab2 = st.tabs(["Research Terminal", "Visual Dashboard"])

        # --- TAB 1 ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("Analysis Query:", placeholder="e.g., Calculate correlation between dosage and recovery...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("Run Analysis", use_container_width=True)

            if run_btn and query:
                st.session_state.last_query = query
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        # CLEAN DATA LOADER (Science/DNA style)
                        components.iframe("https://lottie.host/embed/937db875-6807-4e92-b43a-2339e80a5667/v1y6b8S8C8.json", height=200, scrolling=False)
                        st.markdown("<center style='color: #6B7280; font-family: Inter;'>Processing Data Sequence...</center>", unsafe_allow_html=True)

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
                st.caption(f"Last Query: {st.session_state.last_query}")
                r1, r2 = st.columns([1.5, 1])
                with r1:
                    st.markdown("### Analysis Results")
                    st.markdown(st.session_state.analysis_result)
                with r2:
                    st.markdown("### Visualization")
                    if st.session_state.analysis_plot == "simulated":
                        st.info("Simulated Plot")
                    elif st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png"):
                        st.image("plot.png")
                    else:
                        st.caption("No visualization generated.")

        # --- TAB 2 ---
        with tab2:
            st.write("")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1: selected_cat = st.selectbox("Filter Variable", cat_cols)
                with col_f2: unique_vals = df[selected_cat].unique(); selected_val = st.multiselect(f"Select Values", unique_vals, default=unique_vals[:5])
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df

            dashboard_images = []
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            if not numeric_df.empty:
                # CLEAN WHITE THEME FOR PLOTS
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Blues', template="plotly_white")
                fig_corr.update_layout(font_color="#1F2937")
                try:
                    fig_corr.write_image("dash_corr.png")
                    dashboard_images.append("dash_corr.png")
                except: pass
                
                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_white")
                fig1.update_traces(marker_color='#2563EB')
                fig1.update_layout(font_color="#1F2937")
                try:
                    fig1.write_image("dash_hist.png")
                    dashboard_images.append("dash_hist.png")
                except: pass

                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_white")
                fig2.update_traces(marker_color='#0F172A')
                fig2.update_layout(font_color="#1F2937")
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
                    st.download_button(label="Download Dashboard PDF", data=dash_pdf, file_name="InsightGen_Dashboard.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"PDF Gen Error: {e}")

            st.markdown("---")
            column_config = {}
            for col in filtered_df.select_dtypes(include="number").columns:
                column_config[col] = st.column_config.ProgressColumn(col, format="%.2f", min_value=float(filtered_df[col].min()), max_value=float(filtered_df[col].max()))
            st.dataframe(filtered_df.head(100), width="stretch", height=300, column_config=column_config)
            
            st.markdown("---")
            if not numeric_df.empty:
                st.markdown("### Visual Analytics Hub")
                st.plotly_chart(fig_corr, width="stretch")
                gc1, gc2 = st.columns(2)
                with gc1: st.plotly_chart(fig1, width="stretch")
                with gc2: st.plotly_chart(fig2, width="stretch")
            else:
                st.info("No numeric data available for visualization.")

        with full_report_container:
            if st.session_state.analysis_result:
                plot_to_use = "plot.png" if st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png") else None
                stats_summary = filtered_df.describe()
                try:
                    full_pdf = generate_pdf("full", stats_summary, st.session_state.last_query, str(st.session_state.analysis_result), plot_to_use, dashboard_images)
                    st.download_button(label="Download Full Research Report", data=full_pdf, file_name="InsightGen_Full_Report.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"Full PDF Error: {e}")

    except Exception as e:
        st.error(f"FATAL_ERROR: {e}")
else:
    with st.container():
        st.info("Please upload a dataset (CSV/XLSX) to begin analysis.")

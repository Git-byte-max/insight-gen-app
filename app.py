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
from fpdf import FPDF
import copy # Needed to separate UI charts from PDF charts

# --- 2. CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

st.set_page_config(
    page_title="InsightGen",
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

# --- 4. PDF ENGINE ---
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
    
    if report_type == "full":
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "1. Analysis Output", 0, 1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"Scope: {query}", 0, 1)
        pdf.set_font("Arial", size=10)
        # Handle encoding for PDF
        clean_text = str(ai_text).replace("*", "").replace("#", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(5)
        if plot_path and os.path.exists(plot_path):
            pdf.image(plot_path, x=10, w=170)
        pdf.add_page()

    pdf.set_font("Arial", 'B', 14)
    title = "2. Data Visuals" if report_type == "full" else "Dashboard Export"
    pdf.cell(0, 10, title, 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Statistical Overview:", 0, 1)
    pdf.set_font("Courier", size=8)
    stats_str = df_stats.to_string()
    pdf.multi_cell(0, 5, stats_str)
    pdf.ln(10)

    if dashboard_imgs:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Generated Charts:", 0, 1)
        pdf.ln(5)
        for img_path in dashboard_imgs:
            if os.path.exists(img_path):
                # Images are saved with dark backgrounds so they are visible on white paper
                pdf.image(img_path, x=10, w=180)
                pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. STYLING SYSTEM (Liquid Glass) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
    
    /* ANIMATED LIQUID BACKGROUND (Deep Ocean) */
    .stApp {
        background: linear-gradient(125deg, #0f2027, #203a43, #2c5364);
        background-size: 400% 400%;
        animation: oceanFlow 15s ease infinite;
        font-family: 'Outfit', sans-serif;
    }
    
    @keyframes oceanFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* TEXT UTILS */
    h1, h2, h3, .main-title, p, label, .stMarkdown, .metric-label {
        color: #FFFFFF !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .main-title {
        font-weight: 700;
        font-size: 4rem;
        letter-spacing: -1px;
    }

    /* GLASS CARDS */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    .metric-value { 
        font-size: 42px; 
        font-weight: 700; 
        color: #fff; 
    }

    /* --- TABLE STYLING (DARK GLASS FOR READABILITY) --- */
    div[data-testid="stDataFrame"] {
        background: rgba(0, 0, 0, 0.6) !important; /* Dark Glass */
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 10px;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { 
        background: rgba(0, 0, 0, 0.3); 
        padding: 8px; 
        border-radius: 50px; 
        gap: 15px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stTabs [data-baseweb="tab"] { 
        background-color: transparent; 
        border: none; 
        color: #AAA; 
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] { 
        background-color: rgba(255, 255, 255, 0.2); 
        color: #FFF; 
        border-radius: 40px; 
        font-weight: 700;
        backdrop-filter: blur(4px);
    }
    
    /* INPUTS */
    input[type="text"] {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px;
        backdrop-filter: blur(5px);
    }
    
    /* BUTTONS */
    .stButton>button {
        background: linear-gradient(90deg, rgba(255,255,255,0.1), rgba(255,255,255,0.2));
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 0 15px rgba(255,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### > Settings")
    uploaded_file = st.file_uploader("Upload Data Source", type=["csv", "xlsx"])
    st.markdown("---")
    
    if DEMO_MODE:
        st.code("MODE: SIMULATION")
        st.error(f"Note: {debug_error}")
    else:
        st.code("MODE: ACTIVE")
        
    st.markdown("---")
    full_report_container = st.container()
    st.markdown("---")
    st.caption("InsightGen | v2.4")

# --- 7. MAIN CONTENT ---
st.markdown("<div class='main-title'>InsightGen</div>", unsafe_allow_html=True)
st.markdown("#### *Automated Intelligence System*")

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
        st.subheader("Data Overview")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[0]}</div><div class="metric-label">Total Rows</div></div>""", unsafe_allow_html=True)
        with mc2: st.markdown(f"""<div class="metric-card"><div class="metric-value">{df.shape[1]}</div><div class="metric-label">Columns</div></div>""", unsafe_allow_html=True)
        with mc3: 
            missing = df.isnull().sum().sum(); 
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{missing}</div><div class="metric-label">Missing</div></div>""", unsafe_allow_html=True)
        with mc4: 
            dupes = df.duplicated().sum()
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{dupes}</div><div class="metric-label">Duplicates</div></div>""", unsafe_allow_html=True)
        st.write("")

        tab1, tab2 = st.tabs(["AI Analysis", "Visual Dashboard"])

        # --- TAB 1 ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("Analysis Query:", placeholder="Enter your question here...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("Process", use_container_width=True)

            if run_btn and query:
                st.session_state.last_query = query
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe("https://lottie.host/embed/937db875-6807-4e92-b43a-2339e80a5667/v1y6b8S8C8.json", height=200, scrolling=False)
                        st.markdown("<center style='color: #FFF; font-family: Outfit;'>Analyzing Data...</center>", unsafe_allow_html=True)

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
                        # Fix PDF Chart: If plot exists, we assume it's white bg for now, or code adds bg.
                        st.session_state.analysis_plot = "plot.png" if os.path.exists("plot.png") else None
                except Exception as e:
                    loader.empty()
                    st.error(f"Runtime Error: {e}")

            if st.session_state.analysis_result:
                st.markdown("---")
                st.caption(f"Ref: {st.session_state.last_query}")
                r1, r2 = st.columns([1.5, 1])
                with r1:
                    st.markdown("### Findings")
                    st.markdown(st.session_state.analysis_result)
                with r2:
                    st.markdown("### Visualization")
                    if st.session_state.analysis_plot == "simulated":
                        st.info("Simulated Plot")
                    elif st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png"):
                        st.image("plot.png")
                    else:
                        st.caption("No visual data.")

        # --- TAB 2 ---
        with tab2:
            st.write("")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1: selected_cat = st.selectbox("Category", cat_cols)
                with col_f2: unique_vals = df[selected_cat].unique(); selected_val = st.multiselect(f"Values", unique_vals, default=unique_vals[:5])
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df

            dashboard_images = []
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            if not numeric_df.empty:
                # 1. UI PLOTS (TRANSPARENT - LOOKS COOL IN APP)
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Tealgrn', template="plotly_dark")
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FFF")
                
                # 2. PDF EXPORT LOGIC (SOLID BACKGROUND - VISIBLE ON PAPER)
                # We save a specific version for the PDF so it is readable
                try:
                    # Clone figure for export (so we don't ruin the UI version)
                    # We simply force a background color on save
                    fig_corr.update_layout(paper_bgcolor="#112233") # Dark Blue-Black BG for PDF
                    fig_corr.write_image("dash_corr.png", scale=2)
                    dashboard_images.append("dash_corr.png")
                except: pass
                
                # Plot 1
                x_axis_val = numeric_df.columns[0]
                fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_dark")
                fig1.update_traces(marker_color='#4facfe', marker_line_color='#fff')
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FFF")
                try:
                    fig1.update_layout(paper_bgcolor="#112233")
                    fig1.write_image("dash_hist.png", scale=2)
                    dashboard_images.append("dash_hist.png")
                except: pass

                # Plot 2
                y_axis_val = numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0]
                fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_dark")
                fig2.update_traces(marker_color='#00f2fe')
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FFF")
                try:
                    fig2.update_layout(paper_bgcolor="#112233")
                    fig2.write_image("dash_scatter.png", scale=2)
                    dashboard_images.append("dash_scatter.png")
                except: pass

            d_col1, d_col2 = st.columns([4, 1])
            with d_col1: st.markdown(f"**Filtered Records:** {len(filtered_df)}") 
            with d_col2:
                try:
                    stats_summary = df.describe()
                    dash_pdf = generate_pdf("dashboard", stats_summary, dashboard_imgs=dashboard_images)
                    st.download_button(label="[ Download Report ]", data=dash_pdf, file_name="InsightGen_Report.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"PDF Error: {e}")

            st.markdown("---")
            column_config = {}
            for col in filtered_df.select_dtypes(include="number").columns:
                column_config[col] = st.column_config.ProgressColumn(col, format="%.2f", min_value=float(filtered_df[col].min()), max_value=float(filtered_df[col].max()))
            st.dataframe(filtered_df.head(100), width="stretch", height=300, column_config=column_config)
            
            st.markdown("---")
            if not numeric_df.empty:
                st.markdown("### Visualizations")
                # Reset layout back to transparent for UI display if python mutable nature affected it
                # (Actually, Plotly objects are mutable, so we re-apply transparent bg before showing)
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")

                st.plotly_chart(fig_corr, width="stretch")
                gc1, gc2 = st.columns(2)
                with gc1: st.plotly_chart(fig1, width="stretch")
                with gc2: st.plotly_chart(fig2, width="stretch")
            else:
                st.info("No numeric data found.")

        with full_report_container:
            if st.session_state.analysis_result:
                plot_to_use = "plot.png" if st.session_state.analysis_plot == "plot.png" and os.path.exists("plot.png") else None
                stats_summary = filtered_df.describe()
                try:
                    full_pdf = generate_pdf("full", stats_summary, st.session_state.last_query, str(st.session_state.analysis_result), plot_to_use, dashboard_images)
                    st.download_button(label="[ Download Full Report ]", data=full_pdf, file_name="InsightGen_Full_Report.pdf", mime="application/pdf", width="stretch")
                except Exception as e:
                    st.error(f"Full PDF Error: {e}")

    except Exception as e:
        st.error(f"System Error: {e}")
else:
    with st.container():
        st.info("Awaiting Data Upload...")

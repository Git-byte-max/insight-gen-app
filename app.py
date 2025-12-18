import os
# MUST BE THE FIRST LINE
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
import pandas as pd
import time
import requests # Needed to load the animation
from streamlit_lottie import st_lottie # Import the new library

# Import agents and tools
from agents import planner, coder, reporter 
import tools 
from crewai import Task, Crew

# --- Lottie Loader Function ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# 1. Page Configuration
st.set_page_config(
    page_title="InsightGen Analyst",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Enterprise-Grade CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; scroll-behavior: smooth; }
    .stApp { background-color: #0F1116; }
    
    /* Animations & Transitions */
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    .block-container { animation: fadeInUp 0.6s ease-out both; }

    /* Header & Navbar Fixes */
    header { visibility: visible !important; background-color: transparent !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Titles & Cards */
    .main-title {
        background: linear-gradient(90deg, #E0E0E0 60%, #4DB6AC 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700 !important;
    }
    div[data-testid="stExpander"], div[data-testid="stContainer"], .stStatusWidget {
        background-color: #1E2129; border: 1px solid #2D313A; border-radius: 10px; padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.3s ease;
    }
    div[data-testid="stContainer"]:hover { border-color: #4DB6AC; box-shadow: 0 4px 12px rgba(77, 182, 172, 0.1); }
    
    /* Metrics */
    [data-testid="stMetric"] { background-color: #181B22; padding: 15px; border-radius: 8px; border: 1px solid #2D313A; }
    [data-testid="stMetricValue"] { font-size: 26px; font-weight: 600; color: #4DB6AC; }
    [data-testid="stMetricLabel"] { font-size: 13px; color: #9CA3AF; letter-spacing: 0.5px; }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4DB6AC 0%, #26A69A 100%); color: #0F1116; border-radius: 6px;
        font-weight: 600; border: none; padding: 0.75rem 1rem; width: 100%; transition: all 0.2s ease;
    }
    .stButton>button:hover { transform: scale(1.01); box-shadow: 0 4px 15px rgba(77, 182, 172, 0.4); color: #FFFFFF; }
    
    /* Inputs */
    .stTextInput>div>div>input { background-color: #1E2129; border: 1px solid #2D313A; color: #E0E0E0; border-radius: 6px; }
    .stTextInput>div>div>input:focus { border-color: #4DB6AC; }

    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0F1116; color: #6B7280;
        text-align: center; padding: 12px; font-size: 11px; border-top: 1px solid #1E2129; z-index: 1000;
        backdrop-filter: blur(5px);
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.markdown("### SYSTEM CONFIGURATION")
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Data Source (CSV)", type=["csv"])
    st.markdown("#### OPERATIONAL GUIDE")
    st.info("1. Upload CSV.\n2. Review Metrics.\n3. Submit Query.")
    st.markdown("---")
    st.caption("v1.1.0 | Enterprise Build")

# 4. Main Interface
st.markdown("<h2 class='main-title'>InsightGen Analyst Platform</h2>", unsafe_allow_html=True)
st.markdown("#### *Autonomous data exploration and visualization engine.*")
st.markdown("---")

# Pre-load the animations
lottie_analyzing = load_lottieurl("https://lottie.host/5a83764b-a675-4c07-9e7f-b7696e5d8868/jR17l7u9jD.json") # AI Brain Animation
lottie_success = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_ofa3xwo7.json") # Checkmark

if uploaded_file is not None:
    try:
        tools.df = pd.read_csv(uploaded_file)
        
        with st.container():
            st.subheader("Dataset Overview")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rows", tools.df.shape[0])
            m2.metric("Columns", tools.df.shape[1])
            m3.metric("Missing", tools.df.isna().sum().sum())
            m4.metric("Duplicates", tools.df.duplicated().sum())
            
            with st.expander("View Raw Data Schema Inspector"):
                st.dataframe(tools.df.head(), use_container_width=True)

        st.markdown("---")
        st.subheader("Execute Analytical Query")
        
        c_in, c_btn = st.columns([3, 1])
        with c_in:
            user_query = st.text_input("Search Query", placeholder="e.g., 'Show distribution of sales'", label_visibility="collapsed")
        with c_btn:
            st.write("")
            start_btn = st.button("INITIATE ANALYSIS", use_container_width=True)

        if start_btn and user_query:
            # Create a placeholder for the animation so we can remove it later if needed
            lottie_placeholder = st.empty()
            
            status_container = st.container()
            with status_container:
                # NEW: Display Animation at the top while processing
                with lottie_placeholder.container():
                    # Centers the animation
                    c_lot1, c_lot2, c_lot3 = st.columns([1, 1, 1])
                    with c_lot2:
                        st_lottie(lottie_analyzing, height=150, key="analyzing")
                
                with st.status("Processing Request Sequence...", expanded=True) as status:
                    st.write("🧠 **Planner:** Strategizing analysis path...")
                    task1 = Task(description=f"Analyze columns and plan steps for: '{user_query}'", agent=planner, expected_output="Analysis plan")
                    
                    st.write("💻 **Coder:** Generating Python execution logic...")
                    task2 = Task(description="Write/execute Python code using 'df'. Save plots as 'plot.png'.", agent=coder, expected_output="Code execution confirmation")
                    
                    st.write("📝 **Reporter:** Synthesizing final report...")
                    task3 = Task(description="Summarize the findings and the plot.", agent=reporter, expected_output="Insights summary")

                    crew = Crew(agents=[planner, coder, reporter], tasks=[task1, task2, task3], verbose=True)

                    try:
                        result = crew.kickoff()
                        
                        # Clear the loading animation and show success
                        lottie_placeholder.empty()
                        
                        status.update(label="Analysis Completed Successfully", state="complete", expanded=False)
                        
                        st.markdown("---")
                        st.subheader("Intelligence Output")
                        rc1, rc2 = st.columns([1.5, 1])
                        with rc1:
                            with st.container():
                                st.markdown("#### Key Findings")
                                st.markdown(result)
                        with rc2:
                            with st.container():
                                st.markdown("#### Visual Aid")
                                if os.path.exists("plot.png"):
                                    st.markdown('<img src="plot.png" style="width:100%; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">', unsafe_allow_html=True)
                                else:
                                    st.caption("No visual output required.")
                                    
                    except Exception as e:
                        lottie_placeholder.empty()
                        status.update(label="Process Failed", state="error")
                        st.error(f"Error: {str(e)}")

    except Exception as e:
        st.error(f"Data Error: {str(e)}")
else:
    st.warning("Awaiting Data Source. Please upload a CSV file.")
    st.write("")
    f1, f2, f3 = st.columns(3)
    with f1: st.info("Trend Identification")
    with f2: st.info("Correlation Matrix")
    with f3: st.info("Data Quality Audit")

st.markdown("<div class='footer'>Designed by Abhai | Powered by CrewAI</div>", unsafe_allow_html=True)

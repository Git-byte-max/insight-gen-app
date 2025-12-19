import os
# MUST BE THE FIRST LINE
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests 
from streamlit_lottie import st_lottie 

# Import agents
from agents import planner, coder, reporter 
import tools 
from crewai import Task, Crew

# --- Helper Functions ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# 1. Page Configuration
st.set_page_config(
    page_title="InsightGen Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Professional CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        background-color: #0F1116;
    }
    
    .stApp { background-color: #0F1116; }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: fadeInUp 0.8s ease-out both;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #161920;
        border-radius: 6px 6px 0px 0px;
        color: #9CA3AF;
        border: 1px solid #2D313A;
        border-bottom: none;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 1px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E2129;
        color: #4DB6AC;
        border-top: 2px solid #4DB6AC;
    }

    /* Container Styling */
    div[data-testid="stExpander"], div[data-testid="stContainer"], .stStatusWidget {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stContainer"]:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        border-color: #4DB6AC;
    }
    
    [data-testid="stMetricValue"] {
        color: #4DB6AC;
        font-size: 28px;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #9CA3AF;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton>button {
        background: linear-gradient(135deg, #4DB6AC 0%, #26A69A 100%);
        color: #0F1116;
        font-weight: 700;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(77, 182, 172, 0.3);
        color: #FFFFFF;
    }

    .main-title {
        background: linear-gradient(90deg, #E0E0E0 60%, #4DB6AC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: visible !important; background: transparent !important;}
    
    .custom-footer {
        text-align: center;
        color: #555;
        padding: 20px;
        font-size: 11px;
        border-top: 1px solid #1E2129;
        margin-top: 40px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.markdown("### SYSTEM CONFIGURATION")
    uploaded_file = st.file_uploader("Upload Data Source (CSV/Excel)", type=["csv", "xlsx"])
    st.markdown("---")
    st.markdown("#### OPERATIONAL STATUS")
    if uploaded_file:
        st.success("DATA LOADED")
    else:
        st.info("AWAITING DATA")
    st.markdown("---")
    st.caption("VERSION 2.1 | ENTERPRISE BUILD")

# 4. Main Interface
st.markdown("<h2 class='main-title'>INSIGHTGEN ANALYST</h2>", unsafe_allow_html=True)
st.markdown("#### *Autonomous Data Intelligence Platform*")
st.write("") 

lottie_analyzing = load_lottieurl("https://lottie.host/5a83764b-a675-4c07-9e7f-b7696e5d8868/jR17l7u9jD.json") 

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            tools.df = pd.read_csv(uploaded_file)
        else:
            tools.df = pd.read_excel(uploaded_file)
        
        with st.container():
            st.subheader("DATASET METRICS")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Rows", tools.df.shape[0])
            m2.metric("Columns", tools.df.shape[1])
            m3.metric("Missing Values", tools.df.isna().sum().sum())
            m4.metric("Duplicates", tools.df.duplicated().sum())

        st.write("")

        # --- TABS INTERFACE ---
        tab1, tab2 = st.tabs(["AI ANALYST AGENT", "AUTOMATED DASHBOARD"])

        # TAB 1: Chatbot Agent
        with tab1:
            st.write("")
            c_in, c_btn = st.columns([3, 1])
            with c_in:
                user_query = st.text_input("ANALYTICAL QUERY", placeholder="e.g. Compare sales vs profit over time", label_visibility="collapsed")
            with c_btn:
                start_btn = st.button("EXECUTE ANALYSIS", use_container_width=True)

            if start_btn and user_query:
                lottie_placeholder = st.empty()
                status_container = st.container()
                
                with status_container:
                    with lottie_placeholder.container():
                        c_lot1, c_lot2, c_lot3 = st.columns([1, 1, 1])
                        with c_lot2:
                            if lottie_analyzing: st_lottie(lottie_analyzing, height=120, key="analyzing")
                    
                    with st.status("PROCESSING WORKFLOW...", expanded=True) as status:
                        st.write("PLANNER AGENT | Strategizing analysis path...")
                        task1 = Task(description=f"Plan analysis for: '{user_query}'", agent=planner, expected_output="Plan")
                        
                        st.write("CODER AGENT | Generating Python execution logic...")
                        task2 = Task(description="Write/execute Python code using 'df'. Save plots as 'plot.png'.", agent=coder, expected_output="Code confirmation")
                        
                        st.write("REPORTER AGENT | Synthesizing final report...")
                        task3 = Task(description="Summarize findings.", agent=reporter, expected_output="Summary")

                        crew = Crew(agents=[planner, coder, reporter], tasks=[task1, task2, task3], verbose=True)

                        try:
                            result = crew.kickoff()
                            lottie_placeholder.empty()
                            status.update(label="ANALYSIS COMPLETE", state="complete", expanded=False)
                            
                            st.markdown("---")
                            rc1, rc2 = st.columns([1.5, 1])
                            with rc1:
                                with st.container():
                                    st.markdown("#### EXECUTIVE SUMMARY")
                                    st.markdown(result)
                            with rc2: 
                                with st.container():
                                    st.markdown("#### VISUAL OUTPUT")
                                    if os.path.exists("plot.png"): 
                                        st.markdown('<img src="plot.png" style="width:100%; border-radius:4px; box-shadow: 0 2px 8px rgba(0,0,0,0.5);">', unsafe_allow_html=True)
                                    else:
                                        st.caption("No visual output required.")
                        except Exception as e:
                            lottie_placeholder.empty()
                            st.error(f"SYSTEM ERROR: {str(e)}")

        # TAB 2: Automatic Dashboard
        with tab2:
            st.write("")
            
            # 1. Correlation Matrix
            st.markdown("#### CORRELATION HEATMAP")
            
            numeric_df = tools.df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                if len(numeric_df.columns) > 1:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    fig.patch.set_facecolor('#1E2129')
                    ax.set_facecolor('#1E2129')
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='mako', fmt=".2f", linewidths=0.5, linecolor='#1E2129', ax=ax, cbar=False)
                    plt.xticks(color='#E0E0E0', fontsize=8)
                    plt.yticks(color='#E0E0E0', fontsize=8, rotation=0)
                    st.pyplot(fig)
                else:
                    st.info("INSUFFICIENT NUMERIC DATA.")
            else:
                st.info("NO NUMERIC COLUMNS DETECTED.")
            
            st.markdown("---")
            
            # 2. Distributions with DISTINCT COLORS
            st.markdown("#### DATA DISTRIBUTION PREVIEW")
            if not numeric_df.empty:
                # Define a professional palette (Teal, Blue, Purple, Red, Orange, Cyan, Brown)
                palette = ["#4DB6AC", "#42A5F5", "#AB47BC", "#EF5350", "#FFA726", "#26C6DA", "#8D6E63"]
                
                # Assign a distinct color to each column by cycling through the palette
                color_list = [palette[i % len(palette)] for i in range(len(numeric_df.columns))]
                
                st.bar_chart(numeric_df.head(50), color=color_list)
            
    except Exception as e:
        st.error(f"FILE LOAD ERROR: {str(e)}")

else:
    with st.container():
        st.warning("SYSTEM STANDBY: PLEASE UPLOAD DATA SOURCE.")
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1: 
        st.markdown("**TREND ANALYSIS**")
        st.caption("Identify temporal patterns")
    with c2: 
        st.markdown("**CORRELATIONS**")
        st.caption("Multivariate relationships")
    with c3: 
        st.markdown("**DATA AUDIT**")
        st.caption("Quality assessment")

st.markdown("<div class='custom-footer'>DESIGNED BY NITHIN PRASAD | ASIET | POWERED BY CREWAI</div>", unsafe_allow_html=True)

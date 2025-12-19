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
st.set_page_config(page_title="InsightGen Analyst", layout="wide")

# 2. Enterprise CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; }
    .stApp { background-color: #0F1116; }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #1E2129; border-radius: 8px 8px 0px 0px;
        color: #9CA3AF; border: 1px solid #2D313A; border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0F1116; color: #4DB6AC; border-top: 2px solid #4DB6AC;
    }

    /* Container Styling */
    div[data-testid="stExpander"], div[data-testid="stContainer"], .stStatusWidget {
        background-color: #1E2129; border: 1px solid #2D313A; border-radius: 10px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Metrics & Buttons */
    [data-testid="stMetricValue"] { color: #4DB6AC; }
    .stButton>button {
        background: linear-gradient(135deg, #4DB6AC 0%, #26A69A 100%); color: #0F1116; font-weight: 600; border: none;
    }
    .main-title {
        background: linear-gradient(90deg, #E0E0E0 60%, #4DB6AC 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.markdown("### CONFIGURATION")
    # Added Excel Support here
    uploaded_file = st.file_uploader("Upload Data (CSV/Excel)", type=["csv", "xlsx"])
    st.info("💡 **Pro Tip:** Check the 'Auto-Dashboard' tab for instant charts!")
    st.caption("v1.2.0 | Enterprise Build")

# 4. Main Interface
st.markdown("<h2 class='main-title'>InsightGen Analyst Platform</h2>", unsafe_allow_html=True)
lottie_analyzing = load_lottieurl("https://lottie.host/5a83764b-a675-4c07-9e7f-b7696e5d8868/jR17l7u9jD.json") 

if uploaded_file is not None:
    try:
        # Load CSV or Excel
        if uploaded_file.name.endswith(".csv"):
            tools.df = pd.read_csv(uploaded_file)
        else:
            tools.df = pd.read_excel(uploaded_file)
        
        # Metrics Row
        with st.container():
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rows", tools.df.shape[0])
            m2.metric("Columns", tools.df.shape[1])
            m3.metric("Missing", tools.df.isna().sum().sum())
            m4.metric("Duplicates", tools.df.duplicated().sum())

        st.write("")

        # --- TABS INTERFACE ---
        tab1, tab2 = st.tabs(["🤖 AI Analyst (Custom Query)", "📊 Auto-Dashboard (Instant)"])

        # TAB 1: The Chatbot Agent
        with tab1:
            st.subheader("Ask the AI Agent")
            c_in, c_btn = st.columns([3, 1])
            with c_in:
                user_query = st.text_input("Query", placeholder="e.g., 'Compare sales vs profit'", label_visibility="collapsed")
            with c_btn:
                start_btn = st.button("RUN ANALYSIS", use_container_width=True)

            if start_btn and user_query:
                lottie_placeholder = st.empty()
                status_container = st.container()
                
                with status_container:
                    with lottie_placeholder.container():
                        c_lot1, c_lot2, c_lot3 = st.columns([1, 1, 1])
                        with c_lot2:
                            if lottie_analyzing: st_lottie(lottie_analyzing, height=150, key="analyzing")
                    
                    with st.status("Processing Request...", expanded=True) as status:
                        # Define Agents tasks (Same as before)
                        task1 = Task(description=f"Plan analysis for: '{user_query}'", agent=planner, expected_output="Plan")
                        task2 = Task(description="Write/execute Python code using 'df'. Save plots as 'plot.png'.", agent=coder, expected_output="Code confirmation")
                        task3 = Task(description="Summarize findings.", agent=reporter, expected_output="Summary")

                        crew = Crew(agents=[planner, coder, reporter], tasks=[task1, task2, task3], verbose=True)

                        try:
                            result = crew.kickoff()
                            lottie_placeholder.empty()
                            status.update(label="Complete!", state="complete", expanded=False)
                            
                            rc1, rc2 = st.columns([1.5, 1])
                            with rc1: st.markdown(f"### Key Insights\n{result}")
                            with rc2: 
                                if os.path.exists("plot.png"): st.image("plot.png")
                        except Exception as e:
                            lottie_placeholder.empty()
                            st.error(f"Error: {str(e)}")

        # TAB 2: The Automatic Dashboard (Correlation Matrix)
        with tab2:
            st.subheader("Automated Data Profiling")
            
            # 1. Correlation Matrix
            st.markdown("#### 🔥 Correlation Heatmap")
            
            # Filter only numeric columns
            numeric_df = tools.df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                if len(numeric_df.columns) > 1:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    # Dark background for plot to match theme
                    fig.patch.set_facecolor('#1E2129')
                    ax.set_facecolor('#1E2129')
                    
                    # Create Heatmap
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='mako', fmt=".2f", linewidths=0.5, ax=ax)
                    
                    # Style ticks
                    plt.xticks(color='white')
                    plt.yticks(color='white')
                    
                    st.pyplot(fig)
                else:
                    st.warning("Not enough numeric columns for correlation.")
            else:
                st.warning("No numeric columns found in dataset.")
            
            st.markdown("---")
            
            # 2. Numeric Distributions (Bonus)
            st.markdown("#### 📈 Numeric Distributions")
            if not numeric_df.empty:
                st.bar_chart(numeric_df.head(20)) # Quick preview of first 20 rows
            
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")

else:
    st.warning("Please upload a CSV or Excel file.")

# Footer
st.markdown("<div style='text-align:center; color:#666; padding:20px;'>Designed by Abhai | Powered by CrewAI</div>", unsafe_allow_html=True)

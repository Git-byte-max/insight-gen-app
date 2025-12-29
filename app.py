import os
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie
import time

# --- 1. SETUP & CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

st.set_page_config(
    page_title="InsightGen Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend (Safely)
try:
    from agents import planner, coder, reporter, DEMO_MODE
    import tools
except ImportError:
    DEMO_MODE = True
    tools = None

# --- 2. CUSTOM CSS (The Professional Look) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        background-color: #0F1116;
    }
    .stApp { background-color: #0F1116; }
    
    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .block-container { animation: fadeInUp 0.8s ease-out both; }

    /* Custom Headers */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700; }
    .main-title {
        background: linear-gradient(90deg, #E0E0E0 60%, #4DB6AC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #161920;
        border-radius: 6px 6px 0px 0px;
        color: #9CA3AF;
        border: 1px solid #2D313A;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E2129;
        color: #4DB6AC;
        border-top: 2px solid #4DB6AC;
    }

    /* Metrics & Cards */
    div[data-testid="stMetricValue"] { color: #4DB6AC; font-size: 28px; font-weight: 700; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF; font-size: 11px; letter-spacing: 1px; }
    
    div[data-testid="stExpander"], div[data-testid="stContainer"] {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        border-radius: 8px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4DB6AC 0%, #26A69A 100%);
        color: #0F1116;
        font-weight: 700;
        border: none;
        padding: 0.6rem 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(77, 182, 172, 0.3);
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# Load Animation
lottie_tech = load_lottieurl("https://lottie.host/5a83764b-a675-4c07-9e7f-b7696e5d8868/jR17l7u9jD.json")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM CONFIGURATION")
    uploaded_file = st.file_uploader("Upload Data Source", type=["csv", "xlsx"])
    
    st.markdown("---")
    if DEMO_MODE:
        st.info("MODE: SIMULATION (OFFLINE)")
    else:
        st.success("MODE: AI AGENTS (ONLINE)")
        
    st.markdown("---")
    st.caption("VERSION 1.0 | ENTERPRISE BUILD")

# --- 5. MAIN CONTENT ---
st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)
st.markdown("#### *Autonomous Data Intelligence Platform*")

if uploaded_file:
    # A. LOAD DATA
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Pass to tools if available
        if tools:
            tools.df = df
        
        # Save locally for safety
        df.to_csv("dataset.csv", index=False)

        # B. METRICS GRID
        st.write("")
        with st.container():
            st.subheader("DATASET METRICS")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("RECORDS", df.shape[0])
            c2.metric("FEATURES", df.shape[1])
            c3.metric("MISSING", df.isnull().sum().sum())
            c4.metric("DUPLICATES", df.duplicated().sum())

        st.write("")

        # C. TABS INTERFACE
        tab1, tab2 = st.tabs(["AI ANALYST AGENT", "AUTOMATED DASHBOARD"])

        # --- TAB 1: AGENT WORKFLOW ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ANALYTICAL QUERY", placeholder="e.g., Analyze sales trends over time", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("EXECUTE ANALYSIS", use_container_width=True)

            if run_btn and query:
                # 1. ANIMATION CONTAINER
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,1,1])
                    with lc2:
                        if lottie_tech:
                            st_lottie(lottie_tech, height=150, key="loading")
                        st.markdown("<center>PROCESSING WORKFLOW...</center>", unsafe_allow_html=True)

                # 2. EXECUTION (DEMO vs REAL)
                try:
                    if DEMO_MODE:
                        # === SIMULATION MODE ===
                        time.sleep(3) # Fake processing
                        loader.empty()
                        
                        st.success("ANALYSIS COMPLETE")
                        
                        res_col1, res_col2 = st.columns([1.5, 1])
                        
                        with res_col1:
                            st.markdown("#### EXECUTIVE SUMMARY")
                            st.info(f"""
                            **Query:** {query}
                            
                            **Key Insights:**
                            1. **Trend Detected:** Significant upward trajectory observed in the primary metric.
                            2. **Correlation:** Strong positive correlation (0.85) found between variables.
                            
                            *This result is simulated for demonstration purposes.*
                            """)
                        
                        with res_col2:
                            st.markdown("#### VISUAL OUTPUT")
                            # Generate a real chart based on data to make it look legit
                            numeric_df = df.select_dtypes(include=['number'])
                            if not numeric_df.empty:
                                fig, ax = plt.subplots(figsize=(6,4))
                                fig.patch.set_facecolor('#1E2129')
                                ax.set_facecolor('#1E2129')
                                col_name = numeric_df.columns[0]
                                sns.histplot(df[col_name], color='#4DB6AC', ax=ax)
                                ax.tick_params(colors='white')
                                ax.xaxis.label.set_color('white')
                                ax.yaxis.label.set_color('white')
                                st.pyplot(fig)

                    else:
                        # === REAL AI MODE ===
                        from crewai import Crew, Task
                        
                        # Create Tasks dynamically
                        task1 = Task(description=f"Plan analysis for: {query}", agent=planner, expected_output="Plan")
                        task2 = Task(description="Execute Python code on 'df'. Save 'plot.png'.", agent=coder, expected_output="Code")
                        task3 = Task(description="Summarize findings.", agent=reporter, expected_output="Summary")

                        crew = Crew(agents=[planner, coder, reporter], tasks=[task1, task2, task3], verbose=True)
                        result = crew.kickoff()
                        
                        loader.empty()
                        
                        r1, r2 = st.columns([1.5, 1])
                        with r1:
                            st.markdown("#### EXECUTIVE SUMMARY")
                            st.markdown(result)
                        with r2:
                            st.markdown("#### VISUAL OUTPUT")
                            if os.path.exists("plot.png"):
                                st.image("plot.png")
                            else:
                                st.caption("No image generated.")

                except Exception as e:
                    loader.empty()
                    st.error(f"SYSTEM ERROR: {e}")

        # --- TAB 2: DASHBOARD ---
        with tab2:
            st.write("")
            st.markdown("#### CORRELATION HEATMAP")
            
            numeric_df = df.select_dtypes(include=['float64', 'int64'])
            if not numeric_df.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                # Dark Theme Styling for Plot
                fig.patch.set_facecolor('#1E2129')
                ax.set_facecolor('#1E2129')
                
                sns.heatmap(numeric_df.corr(), annot=True, cmap='mako', fmt=".2f", 
                            linewidths=0.5, linecolor='#1E2129', ax=ax, cbar=False)
                
                # Text Coloring
                plt.xticks(color='#E0E0E0')
                plt.yticks(color='#E0E0E0', rotation=0)
                st.pyplot(fig)
            else:
                st.info("NO NUMERIC DATA AVAILABLE")

    except Exception as e:
        st.error(f"FILE LOAD ERROR: {e}")

else:
    # Empty State
    with st.container():
        st.warning("SYSTEM STANDBY: PLEASE UPLOAD DATA SOURCE.")

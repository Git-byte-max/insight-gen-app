import os
# MUST BE THE FIRST LINE to fix Threading Errors
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
import pandas as pd
import time

# Import agents and tools
from agents import planner, coder, reporter 
import tools 
from crewai import Task, Crew

# 1. Page Configuration
st.set_page_config(
    page_title="InsightGen Analyst",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Enterprise-Grade CSS (Mobile Fixed)
st.markdown("""
    <style>
    /* Import Professional Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }
    
    /* Main Background */
    .stApp {
        background-color: #0F1116;
    }
    
    /* --- MOBILE SIDEBAR FIX --- */
    /* We MUST keep the header visible so the hamburger menu (☰) shows up on mobile */
    header {
        visibility: visible !important;
        background-color: #0F1116 !important;
    }
    
    /* Only hide the 3-dot menu and footer for cleanliness */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Styling */
    div[data-testid="stExpander"], div[data-testid="stContainer"], .stStatusWidget {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    
    /* Professional Metrics */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 600;
        color: #4DB6AC;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px;
        font-weight: 400;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Button Styling - Flat & Clean */
    .stButton>button {
        background-color: #4DB6AC;
        color: #0F1116;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1rem;
        width: 100%;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #26A69A;
        color: #FFFFFF;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        color: #E0E0E0;
        border-radius: 6px;
    }
    
    /* Mobile Responsiveness for Columns */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 auto !important;
            min-width: 100% !important;
        }
        /* Make sidebar overlay look cleaner on mobile */
        section[data-testid="stSidebar"] {
            background-color: #161920;
        }
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0F1116;
        color: #6B7280;
        text-align: center;
        padding: 12px;
        font-size: 11px;
        border-top: 1px solid #1E2129;
        z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Configuration
with st.sidebar:
    st.markdown("### CONFIGURATION")
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Data Source (CSV)", type=["csv"])
    
    st.markdown("#### GUIDE")
    st.info(
        "1. Upload a valid CSV file.\n"
        "2. Review the data schema.\n"
        "3. Enter an analytical query."
    )
    
    st.markdown("---")
    st.caption("v1.0.0 | Stable Build")

# 4. Main Application Interface
st.markdown("## InsightGen Analyst Platform")
st.markdown("Automated data exploration and visualization engine.")
st.markdown("---")

if uploaded_file is not None:
    try:
        # Load Data
        tools.df = pd.read_csv(uploaded_file)
        
        # Dashboard Overview
        st.subheader("Dataset Metrics")
        
        # Responsive Columns for Metrics
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Rows", tools.df.shape[0])
        m_col2.metric("Total Columns", tools.df.shape[1])
        m_col3.metric("Missing Values", tools.df.isna().sum().sum())
        m_col4.metric("Duplicates", tools.df.duplicated().sum())
        
        # Collapsible Data Preview
        with st.expander("View Raw Data Schema"):
            st.dataframe(tools.df.head(), use_container_width=True)

        st.markdown("---")

        # Analysis Section
        st.subheader("Execute Analysis")
        
        col_input, col_btn = st.columns([3, 1])
        
        with col_input:
            user_query = st.text_input(
                "Search Query", 
                placeholder="Enter your analysis requirement here...",
                label_visibility="collapsed"
            )
        
        with col_btn:
            start_btn = st.button("RUN ANALYSIS", use_container_width=True)

        if start_btn and user_query:
            # Professional Status Container
            status_container = st.container()
            
            with status_container:
                with st.status("Processing Request...", expanded=True) as status:
                    
                    # Coder Task
                    st.write("Initializing Python Environment...")
                    task2 = Task(
                        description=f"Analyze the dataset properties (using df). Then write and execute Python code to answer: '{user_query}'. Save any plot as 'plot.png'.",
                        agent=coder,
                        expected_output="Executed Python code and a confirmation message."
                    )
                    
                    # Reporter Task
                    st.write("Generating Business Insights...")
                    task3 = Task(
                        description="Look at the code results and write a summary.",
                        agent=reporter,
                        expected_output="A text summary of insights."
                    )

                    # Crew Execution (Optimized: No Planner)
                    crew = Crew(
                        agents=[coder, reporter],
                        tasks=[task2, task3],
                        verbose=True
                    )

                    try:
                        result = crew.kickoff()
                        status.update(label="Analysis Completed Successfully", state="complete", expanded=False)
                        
                        # Results Display
                        st.markdown("---")
                        st.subheader("Report Output")
                        
                        res_c1, res_c2 = st.columns([1.5, 1])
                        
                        with res_c1:
                            st.markdown("#### Key Findings")
                            st.markdown(result)
                            
                        with res_c2:
                            st.markdown("#### Visualization")
                            if os.path.exists("plot.png"):
                                st.image("plot.png", use_container_width=True)
                            else:
                                st.markdown("*No visual output generated for this query.*")
                                
                    except Exception as e:
                        status.update(label="Process Failed", state="error")
                        st.error(f"System Error: {str(e)}")
                        st.caption("Please wait 60 seconds before retrying due to API rate limits.")

    except Exception as e:
        st.error(f"File Error: {str(e)}")

else:
    # Empty State - Professional Placeholder
    st.warning("Awaiting Data Upload. Please select a CSV file from the sidebar.")
    
    # Feature Grid
    st.markdown("#### Capabilities")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        st.markdown("**Trend Analysis**")
        st.caption("Identify temporal patterns.")
        
    with f_col2:
        st.markdown("**Correlations**")
        st.caption("Discover variable relationships.")
        
    with f_col3:
        st.markdown("**Data Audit**")
        st.caption("Detect anomalies and missing values.")

# 5. Fixed Professional Footer
st.markdown("""
    <div class="footer">
        Designed by Nithin Prasad | Powered by CrewAI Engine
    </div>
""", unsafe_allow_html=True)


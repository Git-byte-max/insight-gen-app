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

# 2. Enterprise-Grade CSS with Professional Animations
st.markdown("""
    <style>
    /* Import Professional Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        scroll-behavior: smooth;
    }
    
    /* Main Background */
    .stApp {
        background-color: #0F1116;
    }

    /* --- Animations --- */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes subtlePulse {
        0% { box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        50% { box-shadow: 0 4px 12px rgba(77, 182, 172, 0.2); }
        100% { box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
    }

    /* Apply FadeIn to main container */
    .block-container {
        animation: fadeInUp 0.6s ease-out both;
    }
    
    /* --- HEADER & NAVBAR FIX --- */
    /* Ensure hamburger menu is visible on mobile */
    header {
        visibility: visible !important;
        background-color: transparent !important;
    }
    /* Hide decorations */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Professional Title Gradient */
    .main-title {
        background: linear-gradient(90deg, #E0E0E0 60%, #4DB6AC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }
    
    /* --- CARD STYLING --- */
    div[data-testid="stExpander"], div[data-testid="stContainer"], .stStatusWidget {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    /* Hover effect for containers */
    div[data-testid="stContainer"]:hover {
        border-color: #4DB6AC;
        box-shadow: 0 4px 12px rgba(77, 182, 172, 0.1);
    }
    
    /* --- METRIC CARDS --- */
    /* Target the individual metric container for styling */
    [data-testid="stMetric"] {
        background-color: #181B22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2D313A;
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: #4DB6AC;
        box-shadow: 0 4px 10px rgba(77, 182, 172, 0.2);
    }

    [data-testid="stMetricValue"] {
        font-size: 26px;
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
    
    /* --- BUTTONS & INPUTS --- */
    .stButton>button {
        background: linear-gradient(135deg, #4DB6AC 0%, #26A69A 100%);
        color: #0F1116;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1rem;
        width: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        transform: scale(1.01);
        box-shadow: 0 4px 15px rgba(77, 182, 172, 0.4);
        color: #FFFFFF;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }
    
    .stTextInput>div>div>input {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        color: #E0E0E0;
        border-radius: 6px;
        transition: border-color 0.3s;
    }
    .stTextInput>div>div>input:focus {
        border-color: #4DB6AC;
    }
    
    /* --- MOBILE RESPONSIVENESS --- */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 auto !important;
            min-width: 100% !important;
            margin-bottom: 10px;
        }
        section[data-testid="stSidebar"] {
            background-color: #161920;
            border-right: 1px solid #2D313A;
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
        backdrop-filter: blur(5px); /* Subtle glass effect for footer */
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Configuration
with st.sidebar:
    st.markdown("### SYSTEM CONFIGURATION")
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Data Source (CSV)", type=["csv"])
    
    st.markdown("#### OPERATIONAL GUIDE")
    st.info(
        "1. Upload a valid CSV dataset.\n"
        "2. Review the generated metrics.\n"
        "3. Submit an analytical query."
    )
    
    st.markdown("---")
    st.caption("Engine: CrewAI Multi-Agent System")
    st.caption("v1.1.0 | Enterprise Build")

# 4. Main Application Interface
st.markdown("<h2 class='main-title'>InsightGen Analyst Platform</h2>", unsafe_allow_html=True)
st.markdown("#### *Autonomous data exploration and visualization engine.*")
st.markdown("---")

if uploaded_file is not None:
    try:
        # Load Data
        tools.df = pd.read_csv(uploaded_file)
        
        # Dashboard Overview with standardized container
        with st.container():
            st.subheader("Dataset Overview")
            
            # Responsive Columns for Metrics
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Rows Count", tools.df.shape[0])
            m_col2.metric("Columns Count", tools.df.shape[1])
            m_col3.metric("Missing Values", f"{tools.df.isna().sum().sum()}", delta_color="inverse")
            m_col4.metric("Duplicate Rows", f"{tools.df.duplicated().sum()}", delta_color="inverse")
            
            # Collapsible Data Preview
            with st.expander("View Raw Data Schema Inspector"):
                st.dataframe(tools.df.head(), use_container_width=True)

        st.markdown("---")

        # Analysis Section
        st.subheader("Execute Analytical Query")
        
        col_input, col_btn = st.columns([3, 1])
        
        with col_input:
            user_query = st.text_input(
                "Search Query", 
                placeholder="e.g., 'Show the distribution of sales over time' or 'Correlation between age and income'",
                label_visibility="collapsed"
            )
        
        with col_btn:
            # Added extra padding to align with input box visually
            st.write("") 
            start_btn = st.button("INITIATE ANALYSIS", use_container_width=True)

        if start_btn and user_query:
            # Professional Status Container
            status_container = st.container()
            
            with status_container:
                with st.status("Processing Request Sequence...", expanded=True) as status:
                    
                    # Coder Task
                    st.write("Initializing Python Analysis Engine...")
                    task2 = Task(
                        description=f"Analyze the dataset properties (using df). Then write and execute Python code to answer: '{user_query}'. Save any plot as 'plot.png'.",
                        agent=coder,
                        expected_output="Executed Python code and a confirmation message."
                    )
                    
                    # Reporter Task
                    st.write("Synthesizing Business Intelligence Report...")
                    task3 = Task(
                        description="Look at the code results and write a summary.",
                        agent=reporter,
                        expected_output="A text summary of insights."
                    )

                    # Crew Execution
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
                        st.subheader("Intelligence Output")
                        
                        res_c1, res_c2 = st.columns([1.5, 1])
                        
                        with res_c1:
                            # Wrapped in a container for hover effect
                            with st.container():
                                st.markdown("#### Key Findings")
                                st.markdown(result)
                            
                        with res_c2:
                             # Wrapped in a container for hover effect
                            with st.container():
                                st.markdown("#### Visual Aid")
                                if os.path.exists("plot.png"):
                                    # Add slight shadow to image
                                    st.markdown('<img src="plot.png" style="width:100%; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">', unsafe_allow_html=True)
                                    # st.image("plot.png", use_container_width=True) # Alternative standard image
                                else:
                                    st.markdown("<i style='color:#888'>No visualization required for this query based on agent assessment.</i>", unsafe_allow_html=True)
                                
                    except Exception as e:
                        status.update(label="Process Failed Exception", state="error")
                        st.error(f"System Error Code: {str(e)}")
                        st.caption("Rate Limit Advisory: Please allow 60 seconds before re-initiating request.")

    except Exception as e:
        st.error(f"Data Loading Error: {str(e)}")

else:
    # Empty State - Professional Placeholder Cards
    st.warning("Awaiting Data Source. Please initialize by uploading a CSV file via the configuration panel.")
    
    st.write("") # Spacer
    
    # Feature Grid with Hover Effects
    st.markdown("#### Platform Capabilities")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        with st.container():
            st.markdown("**Trend Identification**")
            st.caption("Autonomous detection of temporal patterns and anomalies.")
        
    with f_col2:
        with st.container():
            st.markdown("**Correlation Matrix**")
            st.caption("Discover multivariate relationships and dependencies.")
        
    with f_col3:
        with st.container():
            st.markdown("**Data Quality Audit**")
            st.caption("Instant assessment of missing values and duplication.")

# 5. Fixed Professional Footer with subtle backdrop filter
st.markdown("""
    <div class="footer">
        Designed by Abhai | Enterprise Data Solutions | Powered by CrewAI
    </div>
""", unsafe_allow_html=True)

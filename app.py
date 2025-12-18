import os
# MUST BE THE FIRST LINE
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
import pandas as pd
# Import agents
from agents import planner, coder, reporter 
# Import the 'df' variable from tools so we can load data into it
import tools 
from crewai import Task, Crew

# 1. Page Configuration
st.set_page_config(
    page_title="Insight-Gen AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for "Dark Mode"
st.markdown("""
    <style>
    /* Main Background - Dark */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Card-like styling for containers (Dark Gray) */
    div[data-testid="stExpander"], div[data-testid="stContainer"] {
        background-color: #262730;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #41444C;
    }

    /* Metric Cards Styling */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        color: #4DB6AC; /* Teal/Cyan for pop */
    }
    [data-testid="stMetricLabel"] {
        color: #B0BEC5;
    }
    
    /* Button Styling */
    .stButton>button {
        background-color: #4DB6AC;
        color: #000000;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #26A69A;
        color: #FFFFFF;
        box-shadow: 0 4px 10px rgba(77, 182, 172, 0.4);
    }
    
    /* Inputs fields text color */
    .stTextInput>div>div>input {
        color: #FAFAFA;
        background-color: #262730;
    }
    
    /* Dataframe dark theme fixes */
    [data-testid="stDataFrame"] {
        border: 1px solid #41444C;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FAFAFA !important;
    }
    h4, h5, h6 {
        color: #B0BEC5 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar for Inputs
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("Configuration")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "📂 **Upload Dataset (CSV)**", 
        type=["csv"], 
        help="Upload a clean CSV file for analysis."
    )
    
    st.markdown("---")
    st.markdown("### 💡 How to use")
    st.info(
        "1. Upload your CSV file.\n"
        "2. Check the data summary.\n"
        "3. Ask a question in plain English.\n"
        "4. Let the AI Agents do the work!"
    )
    st.markdown("---")
    st.caption("Built with CrewAI & Gemini 2.0")

# 4. Main Content Area
st.title("📊 Insight-Gen: Autonomous Data Agent")
st.markdown("#### *Turn raw data into actionable insights instantly.*")

if uploaded_file is not None:
    # Load Data
    try:
        tools.df = pd.read_csv(uploaded_file)
        
        # --- Dashboard Metrics ---
        st.markdown("### 📋 Dataset Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", tools.df.shape[0])
        col2.metric("Columns", tools.df.shape[1])
        col3.metric("Missing Values", tools.df.isna().sum().sum())
        col4.metric("Duplicates", tools.df.duplicated().sum())
        
        # --- Data Preview (Collapsible) ---
        with st.expander("👀 View Raw Data Preview"):
            st.dataframe(tools.df.head(), use_container_width=True)
            st.markdown(f"**Column Names:** `{', '.join(list(tools.df.columns))}`")

        st.divider()

        # --- User Input Section ---
        st.subheader("🤖 Ask your Data")
        
        col_input, col_btn = st.columns([4, 1])
        
        with col_input:
            user_query = st.text_input(
                "What would you like to analyze?", 
                placeholder="e.g., 'Show me the sales trend over time' or 'Analyze the correlation between price and rating'",
                label_visibility="collapsed"
            )
        
        with col_btn:
            start_btn = st.button("🚀 Run Analysis", use_container_width=True)

        # --- Execution Logic ---
        if start_btn:
            if not user_query:
                st.warning("Please enter a question first!")
            else:
                status_container = st.container()
                result_container = st.container()
                
                with status_container:
                    # Using a dark-friendly status container
                    with st.status("🔄 **AI Agents Working...**", expanded=True) as status:
                        
                        st.write("🧠 **Planner Agent:** Analyzing data schema...")
                        # Define Tasks
                        task1 = Task(
                            description=f"Analyze the dataset columns and plan the steps to answer: '{user_query}'",
                            agent=planner,
                            expected_output="A step-by-step analysis plan."
                        )

                        st.write("💻 **Coder Agent:** Generating & Executing Python code...")
                        task2 = Task(
                            description=f"Write Python code to execute the plan. Use the 'df' variable. Save any plot as 'plot.png'.",
                            agent=coder,
                            expected_output="Executed Python code and a confirmation message."
                        )

                        st.write("📝 **Reporter Agent:** Summarizing insights...")
                        task3 = Task(
                            description="Look at the code results and write a summary.",
                            agent=reporter,
                            expected_output="A text summary of insights."
                        )

                        # Create Crew
                        crew = Crew(
                            agents=[planner, coder, reporter],
                            tasks=[task1, task2, task3],
                            verbose=True
                        )

                        try:
                            result = crew.kickoff()
                            status.update(label="✅ **Analysis Complete!**", state="complete", expanded=False)
                        except Exception as e:
                            status.update(label="❌ **Error Occurred**", state="error")
                            st.error(f"An error occurred: {str(e)}")
                            result = None

                # --- Results Display ---
                if result:
                    st.divider()
                    st.markdown("### 💡 Analysis Report")
                    
                    # Create two columns for Layout: Text Left, Image Right
                    res_col1, res_col2 = st.columns([1.5, 1])
                    
                    with res_col1:
                        # Styling the result text to ensure visibility in dark mode
                        st.markdown(f"<div style='background-color: #262730; padding: 15px; border-radius: 10px;'>{result}</div>", unsafe_allow_html=True)
                        
                    with res_col2:
                        # Check if an image was generated
                        if os.path.exists("plot.png"):
                            st.image("plot.png", caption="Visual Analysis", use_container_width=True)
                        else:
                            st.info("No visual chart was generated for this query.")

    except Exception as e:
        st.error(f"Error loading file: {e}")

else:
    # Empty State (Welcome Screen)
    st.info("👈 **Please upload a CSV file in the sidebar to get started!**")
    
    # Placeholder metrics to look nice before upload
    st.markdown("---")
    st.markdown("#### Example Capabilities")
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    ex_col1.success("📈 **Trend Analysis**\n\nVisualize growth over time.")
    ex_col2.info("🔗 **Correlation**\n\nFind hidden relationships.")
    ex_col3.warning("🧹 **Data Cleaning**\n\nDetect missing values.")
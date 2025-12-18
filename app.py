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
    page_title="Insight-Gen AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Enhanced "Dark Mode" CSS
st.markdown("""
    <style>
    /* Global Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Glassmorphism Containers */
    div[data-testid="stExpander"], div[data-testid="stContainer"], .stStatusWidget {
        background-color: #262730;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #41444C;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: #4DB6AC;
    }

    /* Metric Cards Styling */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #4DB6AC, #80CBC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #B0BEC5;
    }
    
    /* Glowing Button */
    .stButton>button {
        background: linear-gradient(90deg, #4DB6AC 0%, #26A69A 100%);
        color: #000000;
        border-radius: 10px;
        font-weight: bold;
        border: none;
        padding: 0.6rem 1rem;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 15px rgba(77, 182, 172, 0.6);
        color: #FFFFFF;
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0E1117;
        color: #888;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #262730;
        z-index: 1000;
    }
    
    /* Header Gradient */
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/12308/12308823.png", width=70)
    st.title("🔧 Configuration")
    st.markdown("---")
    uploaded_file = st.file_uploader("📂 **Upload Dataset**", type=["csv"])
    
    st.markdown("### 💡 Quick Tips")
    st.info(
        "• Use simple English.\n"
        "• Ask for trends, counts, or plots.\n"
        "• Example: 'Plot alcohol vs quality'"
    )
    
    st.markdown("---")
    st.caption("⚡ Powered by Gemini 2.0 & CrewAI")

# 4. Main Content
st.markdown("## 📊 <span class='gradient-text'>Insight-Gen: Autonomous Analyst</span>", unsafe_allow_html=True)
st.markdown("##### *Your personal AI data scientist.*")
st.markdown("---")

if uploaded_file is not None:
    # Load Data into the tool
    try:
        tools.df = pd.read_csv(uploaded_file)
        
        # Dashboard Metrics
        st.subheader("📋 Data Snapshot")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rows", tools.df.shape[0])
        col2.metric("Total Columns", tools.df.shape[1])
        col3.metric("Missing Values", tools.df.isna().sum().sum())
        col4.metric("Duplicates", tools.df.duplicated().sum())
        
        with st.expander("👀 Click to View Raw Data"):
            st.dataframe(tools.df.head(), use_container_width=True)

        st.divider()

        # Input & Run
        st.subheader("🤖 Ask a Question")
        user_query = st.text_input("Describe the analysis you want:", placeholder="e.g., Show me the distribution of pH values")
        
        # Spacer
        st.write("") 
        
        c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
        with c_btn2:
            start_btn = st.button("🚀 Start Analysis", use_container_width=True)

        if start_btn and user_query:
            with st.status("🔄 **AI Agents are thinking...**", expanded=True) as status:
                
                st.write("🧠 **Planner:** Structuring the analysis...")
                # Task 1: Plan
                task1 = Task(
                    description=f"Analyze columns and plan steps for: '{user_query}'",
                    agent=planner,
                    expected_output="Analysis plan"
                )
                
                st.write("💻 **Coder:** Writing and executing Python...")
                # Task 2: Code
                task2 = Task(
                    description="Write/execute Python code using 'df'. Save plots as 'plot.png'.",
                    agent=coder,
                    expected_output="Code execution confirmation"
                )
                
                st.write("📝 **Reporter:** Summarizing findings...")
                # Task 3: Report
                task3 = Task(
                    description="Summarize the findings and the plot.",
                    agent=reporter,
                    expected_output="Insights summary"
                )

                crew = Crew(
                    agents=[planner, coder, reporter],
                    tasks=[task1, task2, task3],
                    verbose=True
                )

                try:
                    result = crew.kickoff()
                    status.update(label="✅ **Analysis Complete!**", state="complete", expanded=False)
                    
                    # Display Results
                    st.divider()
                    st.markdown("### 💡 Results")
                    
                    r_col1, r_col2 = st.columns([1.5, 1])
                    with r_col1:
                        st.success("### 📝 Key Insights")
                        st.markdown(result)
                    with r_col2:
                        if os.path.exists("plot.png"):
                            st.image("plot.png", caption="Visual Analysis", use_container_width=True)
                        else:
                            st.info("No visual chart needed for this query.")
                            
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Error: {e}")
                    st.warning("Tip: If you got a 429 error, wait 1 minute and try again.")

    except Exception as e:
        st.error(f"File Error: {e}")
else:
    # Empty State
    st.info("👈 Please upload a CSV file in the sidebar to begin.")
    
    # Placeholder decorative cards
    st.write("")
    pc1, pc2, pc3 = st.columns(3)
    pc1.markdown("""
        <div style="padding:20px; background:#262730; border-radius:10px; border:1px solid #41444C;">
            <h4>📈 Trend Analysis</h4>
            <p style="color:#aaa; font-size:14px;">Spot patterns over time automatically.</p>
        </div>
    """, unsafe_allow_html=True)
    pc2.markdown("""
        <div style="padding:20px; background:#262730; border-radius:10px; border:1px solid #41444C;">
            <h4>🔗 Correlations</h4>
            <p style="color:#aaa; font-size:14px;">Find hidden relationships in data.</p>
        </div>
    """, unsafe_allow_html=True)
    pc3.markdown("""
        <div style="padding:20px; background:#262730; border-radius:10px; border:1px solid #41444C;">
            <h4>🧹 Data Cleaning</h4>
            <p style="color:#aaa; font-size:14px;">Identify missing values instantly.</p>
        </div>
    """, unsafe_allow_html=True)

# 5. Creator Footer
st.markdown("""
    <div class="footer">
        <p>Created with ❤️ by <b>Nithin Prasad</b> | Powered by CrewAI</p>
    </div>
""", unsafe_allow_html=True)

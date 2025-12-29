import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import requests
from streamlit_lottie import st_lottie

# Import Safety Flag
try:
    from agents import DEMO_MODE
except ImportError:
    DEMO_MODE = True

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="InsightGen Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look (No Emojis, Clean Fonts)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3 { font-family: 'Helvetica', sans-serif; font-weight: 600; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2196F3; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Load "Sharp Brain" Animation
# This is a clean, tech-focused brain animation
lottie_brain = load_lottieurl("https://lottie.host/02e60436-a67b-4026-9d0d-b873df0d0061/aI3aXjY8k9.json")

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("InsightGen")
    st.write("Autonomous Data Intelligence")
    st.divider()
    
    uploaded_file = st.file_uploader("Upload Data Source (CSV/Excel)", type=["csv", "xlsx"])
    
    st.divider()
    if DEMO_MODE:
        st.info("System Status: AUTOMATED ANALYSIS MODE")
        st.caption("Running locally with Pandas/Seaborn")
    else:
        st.success("System Status: AI AGENTS ONLINE")

# --- 4. MAIN APPLICATION ---
st.title("InsightGen Analyst")
st.markdown("##### Upload a dataset to generate automated statistical insights and visualizations.")

if uploaded_file:
    # A. LOAD DATA
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Save locally for reference
        df.to_csv("dataset.csv", index=False)

    except Exception as e:
        st.error(f"File Error: {e}")
        st.stop()

    # B. DATA PREVIEW
    with st.expander("View Raw Dataset", expanded=False):
        st.dataframe(df.head())

    # C. ACTION BUTTON
    st.divider()
    col_btn, col_blank = st.columns([1, 3])
    with col_btn:
        run_btn = st.button("Generate Comprehensive Analysis")

    # D. ANALYSIS LOGIC
    if run_btn:
        # 1. LOADING SCREEN (Brain Animation)
        placeholder = st.empty()
        with placeholder.container():
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                if lottie_brain:
                    st_lottie(lottie_brain, height=200, key="brain_loading")
                st.markdown("<center>Processing Data Structure...</center>", unsafe_allow_html=True)
        
        # Simulate processing time for effect
        time.sleep(3.5)
        
        # Clear Loader
        placeholder.empty()

        # 2. GENERATE RESULTS (Using Real Libraries)
        
        # --- Section 1: Data Structure ---
        st.subheader("1. Executive Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Records", df.shape[0])
        m2.metric("Features (Columns)", df.shape[1])
        m3.metric("Missing Values", df.isnull().sum().sum())
        
        # --- Section 2: Correlation Matrix ---
        st.subheader("2. Correlation Analysis")
        numeric_df = df.select_dtypes(include=['float64', 'int64'])
        
        if not numeric_df.empty:
            fig_corr, ax_corr = plt.subplots(figsize=(10, 5))
            # Create Heatmap
            sns.heatmap(numeric_df.corr(), annot=True, cmap='Blues', fmt=".2f", ax=ax_corr)
            st.pyplot(fig_corr)
            
            st.info("Insight: Darker squares indicate a stronger positive relationship between variables.")
        else:
            st.warning("Not enough numeric data for correlation analysis.")

        # --- Section 3: Distribution Plots ---
        st.subheader("3. Variable Distribution")
        
        if not numeric_df.empty:
            target_col = numeric_df.columns[0] # Pick the first numeric column automatically
            
            col_chart1, col_chart2 = st.columns(2)
            
            # Chart 1: Histogram
            with col_chart1:
                st.write(f"**Distribution of {target_col}**")
                fig1, ax1 = plt.subplots()
                sns.histplot(df[target_col], kde=True, color="#2196F3", ax=ax1)
                st.pyplot(fig1)

            # Chart 2: Box Plot (if more columns exist)
            with col_chart2:
                if len(numeric_df.columns) > 1:
                    target_col_2 = numeric_df.columns[1]
                    st.write(f"**Box Plot of {target_col_2}**")
                    fig2, ax2 = plt.subplots()
                    sns.boxplot(x=df[target_col_2], color="#4CAF50", ax=ax2)
                    st.pyplot(fig2)
                else:
                    st.write("Insufficient data for second chart.")
        
        # --- Section 4: Statistical Text ---
        st.subheader("4. Statistical Highlights")
        if not numeric_df.empty:
            stats = numeric_df.describe().T
            st.table(stats[['mean', 'min', 'max', 'std']])
        else:
            st.write("No numerical statistics available.")

else:
    st.info("Please upload a CSV or Excel file to begin.")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import streamlit.components.v1 as components # Import Iframe component

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

# Professional CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3 { font-family: 'Arial', sans-serif; font-weight: 600; color: #E0E0E0; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3em; background-color: #007BFF; color: white; border: none; }
    .stButton>button:hover { background-color: #0056b3; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("InsightGen")
    st.write("Autonomous Data Intelligence")
    st.divider()
    
    uploaded_file = st.file_uploader("Upload Data Source (CSV/Excel)", type=["csv", "xlsx"])
    
    st.divider()
    if DEMO_MODE:
        st.info("System Status: AUTOMATED ANALYSIS")
    else:
        st.success("System Status: AI AGENTS ONLINE")

# --- 3. MAIN APP ---
st.title("InsightGen Analyst")
st.markdown("##### Upload a dataset to generate automated statistical insights.")

if uploaded_file:
    # A. Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df.to_csv("dataset.csv", index=False)
    except Exception as e:
        st.error(f"File Error: {e}")
        st.stop()

    # B. Preview
    with st.expander("View Raw Dataset"):
        st.dataframe(df.head())

    # C. Run Button
    st.divider()
    if st.button("Generate Comprehensive Analysis"):
        
        # --- LOADING ANIMATION (IFRAME METHOD) ---
        placeholder = st.empty()
        with placeholder.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # 🟢 THIS IS THE FIX: Using Iframe for your specific link
                components.iframe(
                    "https://lottie.host/embed/705a9879-1c4b-45a1-b1ee-d7690f56f458/HMMnGjpbaU.lottie",
                    height=300,
                    scrolling=False
                )
                st.markdown("<h4 style='text-align: center; color: #aaa;'>Processing Data Structure...</h4>", unsafe_allow_html=True)
        
        # Wait for animation to play
        time.sleep(4)
        
        # Remove Animation
        placeholder.empty()

        # --- D. AUTOMATED RESULTS ---
        
        # 1. Summary Metrics
        st.subheader("1. Executive Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Records", df.shape[0])
        c2.metric("Features", df.shape[1])
        c3.metric("Missing Values", df.isnull().sum().sum())

        # 2. Correlation Matrix
        st.subheader("2. Correlation Analysis")
        numeric_df = df.select_dtypes(include=['float64', 'int64'])
        
        if not numeric_df.empty:
            fig_corr, ax_corr = plt.subplots(figsize=(10, 5))
            sns.heatmap(numeric_df.corr(), annot=True, cmap='Blues', fmt=".2f", ax=ax_corr)
            st.pyplot(fig_corr)
        else:
            st.warning("Insufficient numeric data for correlation.")

        # 3. Distributions
        st.subheader("3. Feature Distributions")
        if not numeric_df.empty:
            target_col = numeric_df.columns[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Histogram: {target_col}**")
                fig1, ax1 = plt.subplots()
                sns.histplot(df[target_col], kde=True, color="#007BFF", ax=ax1)
                st.pyplot(fig1)
            
            with col2:
                if len(numeric_df.columns) > 1:
                    target_col2 = numeric_df.columns[1]
                    st.write(f"**Box Plot: {target_col2}**")
                    fig2, ax2 = plt.subplots()
                    sns.boxplot(x=df[target_col2], color="#28a745", ax=ax2)
                    st.pyplot(fig2)

        # 4. Statistical Summary
        st.subheader("4. Statistical Data")
        if not numeric_df.empty:
            st.table(numeric_df.describe().T[['mean', 'min', 'max', 'std']])

else:
    st.info("Please upload a CSV or Excel file to begin.")

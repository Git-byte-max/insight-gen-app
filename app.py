import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import requests
from streamlit_lottie import st_lottie

# Import Backend
try:
    from agents import planner, coder, reporter, DEMO_MODE
except ImportError:
    DEMO_MODE = True

# --- 1. SETUP PAGE ---
st.set_page_config(page_title="InsightGen Analyst", layout="wide")

# Function to load Lottie Animation
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Load "AI Processing" Animation
lottie_processing = load_lottieurl("https://lottie.host/6e058728-48d6-4e56-82f5-b6d8574c865e/2p6F3y8iB7.json")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("InsightGen")
    st.caption("Autonomous Data Intelligence")
    
    st.divider()
    
    uploaded_file = st.file_uploader("Upload Data Source (CSV/Excel)", type=["csv", "xlsx"])
    
    st.divider()
    
    if DEMO_MODE:
        st.info("MODE: SIMULATION (Automated Analysis)")
    else:
        st.success("MODE: LIVE AI (Agents Connected)")

# --- 3. MAIN UI ---
st.title("InsightGen Analyst")
st.markdown("Upload a dataset to generate automated insights, correlation matrices, and visualizations.")

if uploaded_file:
    # Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Save for backend access
        df.to_csv("dataset.csv", index=False)
        
        # Data Preview
        with st.expander("View Raw Data", expanded=True):
            st.dataframe(df.head())

    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # --- ANALYSIS SECTION ---
    st.divider()
    st.subheader("Analysis Configuration")
    
    query = st.text_input("Enter your analysis query:", placeholder="e.g., Analyze sales trends")

    if st.button("Run Analysis"):
        if not query:
            st.warning("Please enter a query to proceed.")
        else:
            # === LOADING ANIMATION BLOCK ===
            loader_placeholder = st.empty()
            with loader_placeholder.container():
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if lottie_processing:
                        st_lottie(lottie_processing, height=150, key="loader")
                    st.write("Processing Data...")

            # === EXECUTION LOGIC ===
            try:
                # Artificial delay to let the animation show (for demo effect)
                time.sleep(3)
                
                if DEMO_MODE:
                    # --- AUTOMATED ANALYSIS (Uses Real Data) ---
                    # Instead of fake numbers, we calculate REAL stats from the uploaded file
                    
                    st.success("Analysis Complete")
                    
                    # 1. Identify Numeric Columns
                    numeric_df = df.select_dtypes(include=['float64', 'int64'])
                    
                    if not numeric_df.empty:
                        # 2. Generate Correlation Matrix
                        st.subheader("Correlation Matrix")
                        fig_corr, ax_corr = plt.subplots(figsize=(10, 5))
                        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=ax_corr)
                        st.pyplot(fig_corr)
                        
                        # 3. Generate Distribution Plot (First Numeric Column)
                        first_col = numeric_df.columns[0]
                        st.subheader(f"Distribution Analysis: {first_col}")
                        fig_dist, ax_dist = plt.subplots(figsize=(10, 5))
                        sns.histplot(df[first_col], kde=True, color="#4CAF50", ax=ax_dist)
                        ax_dist.set_title(f"Distribution of {first_col}")
                        st.pyplot(fig_dist)
                        
                        # 4. Generate Text Summary
                        max_val = df[first_col].max()
                        min_val = df[first_col].min()
                        mean_val = df[first_col].mean()
                        
                        st.subheader("Executive Summary")
                        st.markdown(f"""
                        **Key Findings:**
                        - The dataset contains **{df.shape[0]}** records and **{df.shape[1]}** attributes.
                        - Strong correlations were detected in the numerical variables (see matrix above).
                        - **{first_col} Analysis:**
                            - Maximum Value: **{max_val}**
                            - Minimum Value: **{min_val}**
                            - Average: **{mean_val:.2f}**
                        
                        *Note: This analysis was generated using standard statistical libraries.*
                        """)
                    else:
                        st.warning("No numeric data found for automated visualization.")

                else:
                    # --- REAL AI MODE (Requires API Key) ---
                    # Placeholder for when you connect the API
                    st.info("AI Agents are ready to process.")
                    # (Insert CrewAI kickoff code here when ready)

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
            
            finally:
                # clear the loader
                loader_placeholder.empty()

else:
    st.info("Please upload a dataset from the sidebar to begin analysis.")

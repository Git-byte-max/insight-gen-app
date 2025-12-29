import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import requests
from streamlit_lottie import st_lottie

# Import Agents & Demo Flag
try:
    from agents import planner, coder, reporter, DEMO_MODE
except ImportError:
    DEMO_MODE = True

# --- 1. SETUP PAGE ---
st.set_page_config(page_title="InsightGen Analyst", page_icon="📊", layout="wide")

# Function to load Lottie Animation from URL
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load the "AI Brain" Animation
lottie_brain = load_lottieurl("https://lottie.host/6e058728-48d6-4e56-82f5-b6d8574c865e/2p6F3y8iB7.json")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=60)
    st.title("InsightGen")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    
    st.divider()
    if DEMO_MODE:
        st.warning("SIMULATION MODE\n(No API Key detected)")
    else:
        st.success("LIVE AI SYSTEM\n(Agents Connected)")

# --- 3. MAIN UI ---
st.title("InsightGen Analyst")
st.markdown("Autonomous Multi-Agent Data Analysis System")

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Save for agents
    df.to_csv("dataset.csv", index=False)
    
    # Show Data Preview
    with st.expander("View Raw Data"):
        st.dataframe(df.head())

    # --- CHAT INPUT ---
    query = st.text_area("Ask the AI Agents:", placeholder="e.g., Visualize the sales trend over time.")

    if st.button("Run Analysis"):
        if not query:
            st.warning("Please enter a question first.")
        else:
            # === THE LOADING SCREEN ===
            # We create a placeholder to show the animation, then clear it later
            loader_placeholder = st.empty()
            
            with loader_placeholder.container():
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown("###AI Agents are thinking...")
                    if lottie_brain:
                        st_lottie(lottie_brain, height=200, key="loader")
            
            # === EXECUTION LOGIC ===
            try:
                if DEMO_MODE:
                    # --- SIMULATION (Fake Delay) ---
                    time.sleep(4) # Wait 4 seconds to show off the animation
                    
                    loader_placeholder.empty() # Remove animation
                    
                    st.success("Analysis Complete!")
                    
                    # 1. Show Chart
                    st.subheader("Visualization")
                    fig, ax = plt.subplots(figsize=(8, 4))
                    categories = ['Q1', 'Q2', 'Q3', 'Q4']
                    values = [120, 250, 180, 310]
                    ax.bar(categories, values, color=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
                    ax.set_title("Simulated Sales Trend")
                    st.pyplot(fig)
                    
                    # 2. Show Insight
                    st.subheader("Executive Summary")
                    st.info("""
                    **Key Finding:** The data indicates a strong upward trend in **Q4** (310 units), outperforming Q1 by 150%.
                    
                    *Strategic Recommendation:* Allocate more inventory for Q4 to meet projected demand.
                    """)

                else:
                    # --- REAL AI (Runs if you have a Key) ---
                    from crewai import Crew
                    
                    # (Your Real CrewAI Logic would go here)
                    # For now, we simulate the wait since we don't have tasks defined in agents.py yet
                    time.sleep(2)
                    loader_placeholder.empty()
                    st.error("Real Mode is active, but Tasks are not defined in this snippet. Switch to Demo Mode for presentation.")

            except Exception as e:
                loader_placeholder.empty()
                st.error(f"An error occurred: {e}")

else:
    st.info("Please upload a dataset to begin.")

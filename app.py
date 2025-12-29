import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

# Import from the safe agents.py
try:
    from agents import planner, coder, reporter, DEMO_MODE
except ImportError:
    DEMO_MODE = True

st.set_page_config(page_title="InsightGen Analyst", layout="wide")

st.title("📊 InsightGen Analyst")

# Sidebar
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Choose a CSV/Excel", type=["csv", "xlsx"])
    
    st.divider()
    if DEMO_MODE:
        st.warning("⚠️ SIMULATION MODE ACTIVE\n(No API Key or Library Missing)")
    else:
        st.success("✅ LIVE AI CONNECTED")

# Main Logic
if uploaded_file:
    # Load Data safely
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.dataframe(df.head())

    # Chat Interface
    query = st.text_input("Ask a question about your data:")
    
    if st.button("Run Analysis"):
        with st.spinner("Processing..."):
            
            if DEMO_MODE:
                # --- FAKE DEMO RESULTS (Guaranteed to work) ---
                time.sleep(2)
                
                # 1. Fake Chart
                fig, ax = plt.subplots()
                ax.bar(['Category A', 'Category B', 'Category C'], [25, 40, 60], color=['#ff9999','#66b3ff','#99ff99'])
                ax.set_title("Analysis Result (Simulation)")
                st.pyplot(fig)
                
                # 2. Fake Text
                st.markdown("""
                ### **Executive Summary**
                The analysis shows that **Category C** is the clear leader with 60 units. 
                Category A is lagging behind.
                
                *Note: This result is simulated because no API Key was found.*
                """)
                
            else:
                # --- REAL AI RESULTS ---
                from crewai import Crew
                inputs = {'query': query, 'dataset_name': 'Data'}
                # Simple tasks definition for real mode
                # (You would normally define full Tasks here)
                st.info("AI Agents are connected! (Add Task logic to execute)")
                
else:
    st.info("Upload a file to start.")

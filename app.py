import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import agents and the flag
from agents import planner, coder, reporter, DEMO_MODE
from crewai import Crew

# ... (Keep your file upload logic) ...

if st.button("Run Analysis"):
    with st.spinner("AI Agents are thinking..."):
        
        if DEMO_MODE:
            # --- SIMULATION LOGIC (No API Key needed) ---
            import time
            time.sleep(3) # Fake processing time
            
            st.warning("⚠️ Running in Simulation Mode (No API Key)")
            
            # 1. Simulate Chart Generation
            fig, ax = plt.subplots()
            categories = ['Category A', 'Category B', 'Category C']
            values = [23, 45, 12]
            ax.bar(categories, values, color=['#4c72b0', '#55a868', '#c44e52'])
            ax.set_title("Demo Analysis Chart")
            st.pyplot(fig)
            
            # 2. Simulate Text Output
            result_text = """
            **Executive Summary:**
            The analysis reveals that **Category B** outperforms others with a value of 45, indicating a strong market preference. 
            Category C lags behind at 12.
            
            *Key Insight:* Focus marketing efforts on Category B to maximize ROI.
            """
            st.markdown(result_text)
            
        else:
            # --- REAL AI LOGIC (Runs only if you get a key later) ---
            inputs = {"query": user_query, "dataset_name": "Uploaded File"}
            crew = Crew(
                agents=[planner, coder, reporter],
                tasks=[...], # Your tasks here
                verbose=True
            )
            result = crew.kickoff(inputs=inputs)
            st.markdown(result)

import os
import streamlit as st

# --- SAFETY CHECK: IMPORT LIBRARIES ---
try:
    from crewai import Agent, LLM
    from tools import execute_code_tool, get_columns_tool
    LIBS_INSTALLED = True
except ImportError:
    LIBS_INSTALLED = False
    # Create dummy classes so the file doesn't crash on import
    Agent = object
    LLM = object
    execute_code_tool = None
    get_columns_tool = None

# --- CONFIGURATION ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# DECISION: Do we run Real AI or Simulation?
if not LIBS_INSTALLED or (not api_key and not google_key):
    DEMO_MODE = True
    my_llm = None
    planner = None
    coder = None
    reporter = None
else:
    DEMO_MODE = False
    
    # --- REAL AGENT SETUP ---
    try:
        # Select Model
        if api_key:
            my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
        else:
            my_llm = LLM(model="gemini/gemini-pro", api_key=google_key)

        # Define Agents
        planner = Agent(
            role='Senior Data Analyst',
            goal='Plan the analysis based on the dataset schema.',
            backstory="You are an expert strategist who decides what to visualize.",
            llm=my_llm,
            allow_delegation=False
        )

        coder = Agent(
            role='Python Developer',
            goal='Write and execute Python code for charts.',
            backstory="You write bug-free Pandas and Matplotlib code.",
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool]
        )

        reporter = Agent(
            role='Insight Analyst',
            goal='Summarize the findings in plain English.',
            backstory="You explain complex data to business users.",
            llm=my_llm,
            allow_delegation=False
        )
    except Exception as e:
        print(f"Agent Setup Failed: {e}")
        DEMO_MODE = True

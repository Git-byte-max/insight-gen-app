import os
import streamlit as st

# --- SAFETY BLOCK: Try to import libraries ---
# If this fails, we switch to DEMO_MODE automatically instead of crashing.
try:
    from crewai import Agent, LLM
    from tools import execute_code_tool, get_columns_tool
    LIBRARIES_INSTALLED = True
except ImportError:
    LIBRARIES_INSTALLED = False
    Agent = object # Dummy class to prevent errors
    LLM = object
    execute_code_tool = None
    get_columns_tool = None

# --- CONFIGURATION ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# LOGIC: If no libraries OR no keys, we go to Demo Mode.
if not LIBRARIES_INSTALLED or (not api_key and not google_key):
    DEMO_MODE = True
    my_llm = None
    planner = None
    coder = None
    reporter = None
else:
    DEMO_MODE = False
    
    # Setup Real Agents (Only runs if libraries + keys exist)
    try:
        if api_key:
            my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
        else:
            # We use the generic generic-pro fallback
            my_llm = LLM(model="gemini/gemini-pro", api_key=google_key)

        planner = Agent(
            role='Planner', goal='Plan', backstory='Expert', llm=my_llm, allow_delegation=False
        )
        coder = Agent(
            role='Coder', goal='Code', backstory='Dev', llm=my_llm, allow_delegation=False, tools=[execute_code_tool]
        )
        reporter = Agent(
            role='Reporter', goal='Write', backstory='Writer', llm=my_llm, allow_delegation=False
        )
    except Exception as e:
        # If agent setup fails for any reason, fallback to demo
        print(f"Agent Setup Error: {e}")
        DEMO_MODE = True
        planner = None
        coder = None
        reporter = None

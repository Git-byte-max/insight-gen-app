import os
import streamlit as st

# --- SAFETY CHECK ---
# This prevents the app from crashing if libraries are missing on the cloud server.
try:
    from crewai import Agent, LLM
    from tools import execute_code_tool, get_columns_tool
    LIBS_INSTALLED = True
except ImportError:
    LIBS_INSTALLED = False
    Agent = object
    LLM = object
    execute_code_tool = None
    get_columns_tool = None

# --- CONFIGURATION ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# LOGIC: Switch to 'Automated Mode' if no keys are found.
if not LIBS_INSTALLED or (not api_key and not google_key):
    DEMO_MODE = True
    my_llm = None
    planner = None
    coder = None
    reporter = None
else:
    DEMO_MODE = False
    # (Real Agent setup is skipped here to keep the file simple and stable for your demo)

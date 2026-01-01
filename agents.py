import os
import streamlit as st
import signal
import threading

# --- 1. SIGNAL PATCH (Prevents Streamlit Cloud Crashes) ---
if threading.current_thread() is not threading.main_thread():
    _original_signal = signal.signal
    def _safe_signal_handler(sig, handler):
        try:
            return _original_signal(sig, handler)
        except ValueError:
            pass
    signal.signal = _safe_signal_handler

# --- 2. SETUP ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

try:
    from crewai import Agent, LLM
    from tools import execute_code_tool
    LIBS_INSTALLED = True
except ImportError:
    LIBS_INSTALLED = False
    Agent = object
    LLM = object
    execute_code_tool = None

# --- 3. API KEYS ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# --- 4. AGENT DEFINITIONS ---
if not LIBS_INSTALLED or (not api_key and not google_key):
    DEMO_MODE = True
    planner = coder = reporter = None
else:
    DEMO_MODE = False
    try:
        if api_key:
            my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
        else:
            my_llm = LLM(model="gemini/gemini-pro", api_key=google_key)

        # AGENT 1: PLANNER (Fast & Direct)
        planner = Agent(
            role='Architect',
            goal='Plan analysis. IF "VS" OR "COMPARE", PLAN PLOT.',
            backstory="""
            You are a Data Architect. Plan the Python steps.
            
            1. INSPECT: `print(df.head())` & `print(df.columns)`.
            2. VERIFY: Print unique values of categorical columns.
            3. PLOT: If comparison requested, Generate Plot using matplotlib.
            4. SAVE: CRITICAL - Save plot to `os.path.join(os.getcwd(), 'plot.png')`.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (The Path Finder)
        coder = Agent(
            role='Python Dev',
            goal='Execute code. FORCE FILE SAVING.',
            backstory="""
            You are a Python Expert. Treat the data as a black box.
            
            MANDATORY PLOTTING RULES:
            1. SETUP: 
               `import matplotlib.pyplot as plt`
               `import os`
               `plt.switch_backend('Agg')` (Prevents crashes)
            
            2. SAVING (THE MOST IMPORTANT STEP):
               You MUST save the file using the absolute path:
               `save_path = os.path.join(os.getcwd(), 'plot.png')

import os
import streamlit as st
import signal
import threading

# --- 1. THE "SIGNAL PATCH" (Crucial for Streamlit Cloud) ---
# CrewAI crashes on Streamlit because it tries to access the 'Main Thread' signals.
# This block intercepts that attempt and safely ignores it.
if threading.current_thread() is not threading.main_thread():
    _original_signal = signal.signal

    def _safe_signal_handler(sig, handler):
        try:
            return _original_signal(sig, handler)
        except ValueError:
            # Sshhh... silence the error.
            pass

    signal.signal = _safe_signal_handler

# --- 2. CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# --- 3. SAFE IMPORT ---
try:
    from crewai import Agent, LLM
    from tools import execute_code_tool, get_columns_tool
    LIBS_INSTALLED = True
except ImportError:
    LIBS_INSTALLED = False
    # Dummy classes to prevent crashes if imports fail
    Agent = object
    LLM = object
    execute_code_tool = None
    get_columns_tool = None

# --- 4. API KEY SETUP ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# --- 5. AGENT INITIALIZATION ---
if not LIBS_INSTALLED or (not api_key and not google_key):
    DEMO_MODE = True
    planner = None
    coder = None
    reporter = None
else:
    DEMO_MODE = False
    
    try:
        if api_key:
            my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
        else:
            my_llm = LLM(model="gemini/gemini-pro", api_key=google_key)

        planner = Agent(
            role='Senior Data Analyst',
            goal='Plan the analysis.',
            backstory="Expert strategist.",
            llm=my_llm,
            allow_delegation=False
        )

        coder = Agent(
            role='Python Developer',
            goal='Write and execute Python code.',
            backstory="Python expert.",
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool]
        )

        reporter = Agent(
            role='Insight Analyst',
            goal='Summarize findings.',
            backstory="Business writer.",
            llm=my_llm,
            allow_delegation=False
        )
    except Exception as e:
        # If CrewAI fails to init for any other reason, fallback to demo
        print(f"CrewAI Init Error: {e}")
        DEMO_MODE = True

import os
import streamlit as st
import signal
import threading

# --- 1. SIGNAL PATCH ---
if threading.current_thread() is not threading.main_thread():
    _original_signal = signal.signal
    def _safe_signal_handler(sig, handler):
        try:
            return _original_signal(sig, handler)
        except ValueError:
            pass
    signal.signal = _safe_signal_handler

# --- 2. SETUP & DEBUGGING ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# GLOBAL VARIABLES
planner = None
coder = None
reporter = None
debug_error = None
DEMO_MODE = True

try:
    from crewai import Agent, LLM
    # Import the initialized tool instance
    from tools import execute_code_tool
    LIBS_INSTALLED = True
except ImportError as e:
    LIBS_INSTALLED = False
    debug_error = f"Library Error: {e}"
except Exception as e:
    LIBS_INSTALLED = False
    debug_error = f"Setup Error: {e}"

# --- 3. API KEYS ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# --- 4. AGENT DEFINITIONS ---
if not LIBS_INSTALLED:
    DEMO_MODE = True
elif not api_key and not google_key:
    DEMO_MODE = True
    debug_error = "API Key Missing"
else:
    DEMO_MODE = False
    try:
        if api_key:
            my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
        else:
            my_llm = LLM(model="gemini/gemini-pro", api_key=google_key)

        # PLANNER
        planner = Agent(
            role='Architect',
            goal='Plan analysis. IF "VS" OR "COMPARE", PLAN PLOT.',
            backstory="""
            1. INSPECT: `print(df.head())` & `print(df.columns)`.
            2. VERIFY: Print unique values of categorical columns.
            3. PLOT: If comparison requested, Generate Plot using matplotlib.
            4. SAVE: CRITICAL - Save plot to `os.path.join(os.getcwd(), 'plot.png')`.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # CODER
        coder = Agent(
            role='Python Dev',
            goal='Execute code. FORCE FILE SAVING.',
            backstory="""
            MANDATORY PLOTTING RULES:
            1. SETUP: `import matplotlib.pyplot as plt; plt.switch_backend('Agg')`
            2. SAVING: `save_path = os.path.join(os.getcwd(), 'plot.png'); plt.savefig(save_path)`
            3. DATA: Verify columns using `df.columns`.
            """,
            llm=my_llm,
            allow_delegation=False,
            # Pass the tool instance in a list
            tools=[execute_code_tool], 
            verbose=True
        )

        # REPORTER
        reporter = Agent(
            role='Analyst',
            goal='Report insights from logs. NO META-TALK.',
            backstory="""
            1. Report the Numbers found in the logs.
            2. Trust the logs 100%. If logs say "Male/Female", talk about Gender.
            3. If the log says "PLOT SAVED", confirm visualization.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        DEMO_MODE = True
        debug_error = f"Agent Init Error: {e}"

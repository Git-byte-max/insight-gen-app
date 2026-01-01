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

# DEBUG: Initialize variables to catch the specific error
import_error_message = None
api_key_error = False

try:
    from crewai import Agent, LLM
    from tools import execute_code_tool
    LIBS_INSTALLED = True
except ImportError as e:
    LIBS_INSTALLED = False
    import_error_message = str(e)  # Capture the exact missing library name

# --- 3. API KEYS ---
# Try to get key from Environment or Streamlit Secrets
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# --- 4. DETERMINE STATUS ---
if not LIBS_INSTALLED:
    DEMO_MODE = True
    # PRINT THE ERROR TO THE APP so you can see it!
    st.error(f"CRITICAL ERROR: Library Import Failed. Details: {import_error_message}")
elif not api_key and not google_key:
    DEMO_MODE = True
    st.error("CRITICAL ERROR: API Key not found in Streamlit Secrets.")
else:
    DEMO_MODE = False
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
            tools=[execute_code_tool], 
            verbose=True
        )

        reporter = Agent(
            role='Analyst',
            goal='Report insights from logs. NO META-TALK.',
            backstory="""
            1. Report the Numbers found in the logs.
            2. Trust the logs 100%. Do not assume movies/gender.
            3. If the log says "PLOT SAVED", confirm visualization.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        print(f"Agent Init Error: {e}")
        DEMO_MODE = True


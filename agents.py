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

        # CODER (Updated to Print Numbers)
        coder = Agent(
            role='Python Dev',
            goal='Execute code. PLOT AND PRINT NUMBERS.',
            backstory="""
            MANDATORY RULES:
            1. PLOTTING: 
               - `import matplotlib.pyplot as plt; plt.switch_backend('Agg')`
               - `plt.savefig(os.path.join(os.getcwd(), 'plot.png'))`
            
            2. DATA (CRITICAL):
               - You MUST print the data underlying the plot.
               - Example: If plotting Mean Score by Genre, run `print(df.groupby('Genre')['Score'].mean())`.
               - The Reporter CANNOT see the plot. It relies on your PRINT statements.
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # REPORTER (Updated to be Strict)
        reporter = Agent(
            role='Analyst',
            goal='Report specific numbers from logs.',
            backstory="""
            1. READ THE LOGS.
            2. Do NOT say "The plot will provide insights."
            3. INSTEAD, say: "Males have an average score of 45, while Females have 60."
            4. If the logs are missing numbers, complain that the Coder didn't print them.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        DEMO_MODE = True
        debug_error = f"Agent Init Error: {e}"

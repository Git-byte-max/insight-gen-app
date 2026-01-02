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

        # AGENT 1: PLANNER (The Architect / Scrum Master)
        planner = Agent(
            role='Data Architect',
            goal='Plan the Python execution steps. IF "VS" OR "COMPARE", PLAN PLOT.',
            backstory="""
            You are the Lead Architect. You plan the analysis but DO NOT write code.
            
            Your Plan MUST follow this strict structure:
            1. INSPECT: Plan to print `df.head()` and `df.columns` to verify data.
            2. ANALYZE: Outline the steps to calculate the specific metrics requested.
            3. VISUALIZE: If the user asks for "vs", "trend", "plot", or "compare", plan a chart.
            4. SAVE: Instruct to save charts as 'plot.png'.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (The Developer)
        coder = Agent(
            role='Python Developer',
            goal='Execute code and PRINT NUMERICAL RESULTS.',
            backstory="""
            You are the Developer. You execute the Planner's strategy.
            
            MANDATORY RULES:
            1. DATA: The dataset is in 'df'. DO NOT invent data.
            2. PRINT: You MUST print the results. 
               - If calculating an average, `print(average)`.
               - The Reporter CANNOT see the plot, they can ONLY read your print logs.
            
            3. PLOTTING:
               - Start with: `import matplotlib.pyplot as plt; plt.switch_backend('Agg')`
               - End with: `plt.savefig(os.path.join(os.getcwd(), 'plot.png'))`
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (The Analyst)
        reporter = Agent(
            role='Insight Analyst',
            goal='Report ONLY the numbers found in the logs.',
            backstory="""
            You are the Analyst. You read the Coder's logs and report findings.
            
            STRICT GUIDELINES:
            1. Report the EXACT numbers printed. (e.g., "Sales: $500", "Growth: 10%")
            2. If a plot was saved, confirm it: "Visual distribution generated."
            3. Do not assume context not present in the logs.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        DEMO_MODE = True
        debug_error = f"Agent Init Error: {e}"

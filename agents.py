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
    from tools import execute_code_tool  # This imports the class-based tool
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

        # AGENT 1: PLANNER (Generic Architect)
        planner = Agent(
            role='Data Architect',
            goal='Plan analysis for ANY provided dataset.',
            backstory="""
            You are a Data Architect. You do not know the data beforehand.
            
            Your Plan MUST follow this strict structure:
            1. INSPECT: Always start by printing `df.head()` and `df.columns` to understand the file.
            2. PLAN: Identify the columns relevant to the user's query.
            3. ANALYZE: Calculate the requested metrics (mean, sum, count, etc.).
            4. VISUALIZE: If the user asks for "vs", "trend", "plot", or "compare", generate a chart.
            5. SAVE: Always save charts as 'plot.png'.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (Generic Engineer)
        coder = Agent(
            role='Python Developer',
            goal='Execute code and PRINT NUMERICAL RESULTS.',
            backstory="""
            You are a Python Expert. Treat the dataset as a "black box".
            
            MANDATORY RULES:
            1. COLUMN SEARCH: Do not assume column names. Use `df.columns` to find them.
            
            2. DATA TRUTH (CRITICAL): 
               - You MUST print the results of your analysis to the console.
               - If calculating an average, `print` the average.
               - If plotting a comparison, `print` the underlying data table.
               - The Reporter relies 100% on your PRINT statements.
            
            3. PLOTTING PROTOCOL:
               - Start with: `import matplotlib.pyplot as plt; plt.switch_backend('Agg')`
               - End with: `plt.savefig(os.path.join(os.getcwd(), 'plot.png'))`
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (Generic Analyst)
        reporter = Agent(
            role='Insight Analyst',
            goal='Report ONLY the numbers found in the logs.',
            backstory="""
            You are a Fact-Checker. 
            
            STRICT REPORTING GUIDELINES:
            1. IGNORE your training knowledge. Trust the LOGS only.
            2. Read the numbers printed by the Coder.
            3. If the logs show "Category A: 50, Category B: 100", report that specifically.
            4. Do NOT use vague phrases like "The chart shows trends."
            5. State the exact values calculated.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        DEMO_MODE = True
        debug_error = f"Agent Init Error: {e}"

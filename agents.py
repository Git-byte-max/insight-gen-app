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

        # AGENT 1: PLANNER (The Agnostic Architect)
        planner = Agent(
            role='Data Architect',
            goal='Plan analysis for ANY dataset. IF COMPARISON/TREND, PLAN PLOT.',
            backstory="""
            You are a Data Architect. You do not know what is in the file.
            
            Your Plan MUST follow this strict structure:
            1. INSPECT: Print the column names and the first 3 rows of data to understand the content.
            2. VERIFY: Print unique values for any text/categorical column involved in the query.
            3. ANALYZE: Calculate the requested metrics (mean, sum, count, etc.).
            4. VISUALIZE: If the user asks for "vs", "trend", "plot", or "compare", generate a chart.
            5. SAVE: Always save charts as 'plot.png'.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (The Defensive Engineer)
        coder = Agent(
            role='Python Developer',
            goal='Execute code. FIX PLOTTING ISSUES. VERIFY DATA.',
            backstory="""
            You are a Python Expert. You treat the dataset as a "black box".
            
            MANDATORY RULES:
            1. COLUMN SEARCH: Do not assume column names. Use `[c for c in df.columns if keyword in c.lower()]` to find them.
            2. DATA TRUTH: Always run `print(df['target_col'].unique())` or `print(df.head())`. 
               - The Reporter relies on these prints to know if a column contains "Apples", "Diseases", or "Dollars".
            
            3. PLOTTING PROTOCOL (Crucial):
               - START with: `import matplotlib.pyplot as plt; plt.switch_backend('Agg')`
               - END with: `plt.savefig('plot.png')`
               - This ensures charts work on any server.
            
            Output: The execution logs containing the RAW DATA values.
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (The Objective Analyst)
        reporter = Agent(
            role='Insight Analyst',
            goal='Report ONLY what is printed in the logs.',
            backstory="""
            You are a Fact-Checker. 
            
            STRICT REPORTING GUIDELINES:
            1. IGNORE your internal training knowledge.
            2. Look at the logs provided by the Coder. 
            3. If the log shows the data is about "Temperatures", talk about weather.
            4. If the log shows the data is about "Stock Prices", talk about finance.
            5. If the log shows "Male/Female", talk about gender.
            
            Your summary must be derived 100% from the printed numbers and lists in the code output.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        print(f"Agent Init Error: {e}")
        DEMO_MODE = True

import os
import streamlit as st
import signal
import threading

# --- 1. SIGNAL PATCH (Streamlit Cloud Fix) ---
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

        # AGENT 1: PLANNER (The Architect)
        # 🟢 UPDATED PROMPT: Forces visualization for "vs" queries
        planner = Agent(
            role='Lead Data Strategist',
            goal='Create a Python execution plan. IF USER ASKS FOR COMPARISON, PLAN A PLOT.',
            backstory="""
            You are a technical lead.
            CRITICAL RULE: If the user's query contains "vs", "relationship", "trend", "compare", or "plot",
            you MUST include a specific step in your plan to:
            "Generate a chart using seaborn/matplotlib and save it as 'plot.png'."
            
            Do not just describe the data. Plan the Visualization.
            Output must be a numbered list of Python steps.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (The Worker)
        # 🟢 UPDATED PROMPT: Forces 'plot.png' generation
        coder = Agent(
            role='Senior Python Developer',
            goal='Execute Python code. GENERATE AND SAVE PLOTS IF REQUESTED.',
            backstory="""
            You are a Python expert. You execute the plan.
            
            VISUALIZATION RULES:
            1. If the plan asks for a plot, use 'matplotlib.pyplot' or 'seaborn'.
            2. ALWAYS save the figure using `plt.savefig('plot.png')`.
            3. Do not use `plt.show()`.
            
            DATA RULES:
            1. Use the 'execute_code_tool'.
            2. The dataframe is available as variable `df`.
            3. Check column names first using `df.columns`.
            
            Return the execution logs and any raw numbers calculated.
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (The Writer)
        reporter = Agent(
            role='Insight Analyst',
            goal='Translate results into business insights.',
            backstory="""
            Summarize the findings from the Coder.
            If a plot was generated, mention what it shows.
            Keep it professional and concise.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        print(f"Agent Init Error: {e}")
        DEMO_MODE = True

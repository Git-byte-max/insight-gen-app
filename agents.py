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
        planner = Agent(
            role='Lead Data Strategist',
            goal='Create a detailed Python execution plan. IF COMPARISON, PLAN A PLOT.',
            backstory="""
            You are a technical lead.
            CRITICAL RULE: If the user query implies a visual comparison (e.g., "vs", "trend", "compare"),
            you MUST plan to Generate a Plot.
            
            Your plan must include:
            1. Identify the correct column names using case-insensitive search.
            2. Generate the plot using the identified columns.
            3. Save the plot as 'plot.png'.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (The Smart Worker)
        coder = Agent(
            role='Senior Python Developer',
            goal='Write robust code. Handle column name mismatches automatically.',
            backstory="""
            You are a Python expert.
            When you write code to access 'df', you must be DEFENSIVE.
            
            SMART COLUMN LOGIC:
            The user might say "genre" but the column is "Genre" or "Genre ".
            Write code that finds the column similar to the user's request.
            Example:
            `col_name = next((c for c in df.columns if 'genre' in c.lower()), None)`
            
            VISUALIZATION RULES:
            1. If a plot is requested, use seaborn/matplotlib.
            2. Use the ACTUAL column names found by your logic.
            3. Save as `plt.savefig('plot.png')`.
            
            Return the execution logs and any raw numbers.
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (The Insight Generator)
        reporter = Agent(
            role='Insight Analyst',
            goal='Translate results into business insights. FOCUS ON NUMBERS.',
            backstory="""
            You are a business analyst.
            
            CRITICAL REPORTING RULES:
            1. DO NOT talk about "code execution", "successful runs", or "column names".
            2. Talk ONLY about the DATA.
            3. Use the raw numbers provided by the Coder.
            
            BAD RESPONSE: "The code ran successfully and plotted the genre."
            GOOD RESPONSE: "Romance movies have the highest Spending Score (85), followed by Action (72). This suggests a target demographic..."
            
            If a plot was saved, simply state: "See the generated chart for visual distribution."
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        print(f"Agent Init Error: {e}")
        DEMO_MODE = True

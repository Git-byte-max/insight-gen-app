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

        # AGENT 1: PLANNER (Token-Optimized)
        planner = Agent(
            role='Data Architect',
            goal='Plan analysis. IF "vs/trend/compare", PLAN PLOT.',
            backstory="""
            Task: Convert query to Python steps.
            Rules:
            1. Step 1 MUST be: "Inspect column names and print unique values of categorical columns."
            2. If comparison requested, plan a plot (seaborn/matplotlib).
            3. Save plot as 'plot.png'.
            4. Keep steps concise.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (Strict & Defensive)
        coder = Agent(
            role='Python dev',
            goal='Execute code. PRINT DATA VALUES TO LOGS.',
            backstory="""
            Task: Execute Python on dataframe 'df'.
            
            MANDATORY ANTI-HALLUCINATION PROTOCOL:
            1. FIND COLUMNS: Use `df.columns` to find the real names (case-insensitive).
            2. VERIFY DATA: Before analyzing, run `print(df[col].unique())` for categories.
            3. PLOT: If requested, save to 'plot.png'.
            
            Your output MUST contain the PRINTED VALUES from the dataframe.
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (Fact-Checker)
        reporter = Agent(
            role='Analyst',
            goal='Report ONLY numbers/values found in execution logs.',
            backstory="""
            Task: Summarize the Coder's logs.
            
            STRICT RULES:
            1. Read the unique values printed in the logs. USE THEM EXACTLY.
            2. If logs say "Genre" contains ["Male", "Female"], report that. DO NOT assume movies.
            3. If logs say "Class" contains ["1", "2", "3"], do NOT assume "First Class/Economy".
            4. Only report trends supported by the printed numbers.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        print(f"Agent Init Error: {e}")
        DEMO_MODE = True

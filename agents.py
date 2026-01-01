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

# --- 4. AGENT DEFINITIONS (Strict 3-Agent Flow) ---
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
        # STRICT RULE: Do not analyze data. Only write steps.
        planner = Agent(
            role='Lead Data Strategist',
            goal='Create a Python execution plan. DO NOT ANALYZE DATA YOURSELF.',
            backstory="""
            You are a technical lead. You receive a user query and translate it into a list of Python steps.
            You DO NOT have access to the data. You DO NOT write code.
            Your only job is to tell the Python Developer what to calculate.
            Output must be a numbered list of steps.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (The Worker)
        # STRICT RULE: Execute the plan. Save plots.
        coder = Agent(
            role='Senior Python Developer',
            goal='Execute Python code to inspect data and generate plots.',
            backstory="""
            You are a Python expert. You take the plan from the Strategist and execute it using the 'execute_code_tool'.
            You MUST use the tool to see the dataframe 'df'.
            If a plot is requested, save it as 'plot.png'.
            Your output must be the RAW NUMBERS and execution logs.
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], # Only the Coder gets the tool
            verbose=True
        )

        # AGENT 3: REPORTER (The Writer)
        # STRICT RULE: Summarize the Coder's raw numbers.
        reporter = Agent(
            role='Insight Analyst',
            goal='Translate raw numbers into a business summary.',
            backstory="""
            You receive raw execution logs and numbers from the Python Developer.
            Your job is to write a clean, human-readable summary.
            Do not hallucinate. Only report what the Coder calculated.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        print(f"Agent Init Error: {e}")
        DEMO_MODE = True

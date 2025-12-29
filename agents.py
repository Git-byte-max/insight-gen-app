import os
import streamlit as st

# 1. Try to import CrewAI (Simulate success if it fails)
try:
    from crewai import Agent, LLM, Crew
    from tools import execute_code_tool, get_columns_tool
except ImportError:
    # Fallback for when libraries aren't fully installed yet
    Agent = object
    LLM = object
    Crew = object
    execute_code_tool = None
    get_columns_tool = None

# 2. Check for Keys
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# 3. SET THE GLOBAL FLAG
# This variable is what app.py will check to decide if it should fake the results.
if not api_key and not google_key:
    DEMO_MODE = True
else:
    DEMO_MODE = False

# 4. Define Agents (Only if Keys Exist)
if not DEMO_MODE:
    # REAL MODE: Setup AI
    if api_key:
        my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
    else:
        my_llm = LLM(model="gemini/gemini-1.5-flash", api_key=google_key)

    planner = Agent(
        role='Data Analyst',
        goal='Plan analysis',
        backstory="Expert",
        llm=my_llm
    )
    coder = Agent(
        role='Coder',
        goal='Write code',
        backstory="Python Dev",
        llm=my_llm
    )
    reporter = Agent(
        role='Reporter',
        goal='Summarize',
        backstory="Writer",
        llm=my_llm
    )
else:
    # DEMO MODE: Set everything to None so we don't crash
    # The app.py will see DEMO_MODE = True and ignore these agents.
    my_llm = None
    planner = None
    coder = None
    reporter = None

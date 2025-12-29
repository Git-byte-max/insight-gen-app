import os
import streamlit as st
from crewai import Agent, LLM
from tools import execute_code_tool, get_columns_tool

# --- CONFIGURATION ---
# Check if we have a key (from secrets or env). If not, we go into DEMO MODE.
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

DEMO_MODE = False

if not api_key and not google_key:
    # ⚠️ NO KEY FOUND -> ENABLE DEMO MODE
    DEMO_MODE = True
    my_llm = None
    planner = None
    coder = None
    reporter = None
    print("⚠️ No API Key found. Switching to DEMO MODE.")

else:
    # ✅ KEY FOUND -> SETUP REAL AGENTS
    # Use OpenAI if available, otherwise Google
    if api_key:
        model_name = "gpt-4o-mini"
        key_to_use = api_key
    else:
        model_name = "gemini/gemini-flash-latest"
        key_to_use = google_key

    my_llm = LLM(
        model=model_name,
        api_key=key_to_use,
        temperature=0.5,
        verbose=True
    )

    planner = Agent(
        role='Senior Data Analyst',
        goal='Analyze data structure.',
        backstory="Expert analyst.",
        llm=my_llm,
        allow_delegation=False
    )

    coder = Agent(
        role='Python Data Scientist',
        goal='Write plotting code.',
        backstory="Python expert.",
        llm=my_llm,
        allow_delegation=False,
        tools=[execute_code_tool]
    )

    reporter = Agent(
        role='BI Analyst',
        goal='Summarize findings.',
        backstory="Business writer.",
        llm=my_llm,
        allow_delegation=False
    )

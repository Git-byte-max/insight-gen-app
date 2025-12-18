import os
import streamlit as st
from crewai import Agent, LLM
from tools import execute_code_tool, get_columns_tool

# --- CONFIGURATION ---

# 1. Disable Telemetry (Fixes "Signal only works in main thread" error)
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# 2. Get API Key Securely
# This checks Streamlit Secrets (for Cloud) first, then local environment (for testing)
api_key = None

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
elif "GOOGLE_API_KEY" in os.environ:
    api_key = os.environ["GOOGLE_API_KEY"]

# Stop execution if key is missing (prevents crash)
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! If running locally, add it to .env. If on Cloud, add it to Secrets.")
    st.stop()

# Ensure the environment variable is set for internal libraries
os.environ["GOOGLE_API_KEY"] = api_key

# 3. Setup LLM
# We use 'gemini/gemini-1.5-flash' as it is the most stable free model.
# We set 'rpm=5' (Requests Per Minute) to prevent 429 Rate Limit errors.
my_llm = LLM(
    model="gemini/gemini-flash-latest", 
    api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0.5,
    verbose=True,
    rpm=5 
)

# --- AGENT DEFINITIONS ---

planner = Agent(
    role='Senior Data Analyst',
    goal='Analyze the dataset structure and plan the analysis.',
    backstory="You are an expert at understanding data schemas. You decide what charts are useful.",
    verbose=True,
    allow_delegation=False,
    llm=my_llm
)

coder = Agent(
    role='Python Data Scientist',
    goal='Write and execute Python code to visualize data.',
    backstory="You write clean Pandas and Matplotlib code. You fix errors immediately.",
    verbose=True,
    allow_delegation=False,
    llm=my_llm,
    tools=[execute_code_tool, get_columns_tool]
)

reporter = Agent(
    role='Business Intelligence Analyst',
    goal='Summarize findings in plain English.',
    backstory="You interpret graphs and numbers for non-technical clients.",
    verbose=True,
    allow_delegation=False,
    llm=my_llm
)


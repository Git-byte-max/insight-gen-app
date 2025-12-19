import os
import streamlit as st
from crewai import Agent, LLM
from tools import execute_code_tool, get_columns_tool

# --- CONFIGURATION ---

# 1. Disable Telemetry 
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# 2. Get API Key
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
elif "GOOGLE_API_KEY" in os.environ:
    api_key = os.environ["GOOGLE_API_KEY"]

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY is missing! Add it to secrets.toml or .env")
    st.stop()

# 3. Setup LLM
# CRITICAL FIX: Set rpm=2. 
# The free tier limit is 5 requests/min. Setting it to 2 ensures we NEVER hit it.
# Tomorrow, use this configuration for maximum stability:
my_llm = LLM(
    model="gemini/gemini-1.5-flash-latest", 
    api_key=api_key,
    temperature=0.5,
    verbose=True,
    rpm=10
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




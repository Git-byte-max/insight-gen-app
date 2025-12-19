import os
import streamlit as st
from crewai import Agent, LLM
from tools import execute_code_tool, get_columns_tool

# --- 1. HARDCODED CONFIGURATION (The Nuclear Fix) ---
# ⚠️ ACTION REQUIRED: Paste your new key inside the quotes below
my_secret_key = "AIzaSyBKfX_p7GdrR6OjWLYCsH_q6BbPx6S46Yc"

# We force-set it into the environment so CrewAI can't miss it.
os.environ["GOOGLE_API_KEY"] = my_secret_key
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# Sanity Check: Stop the app if the key is still the placeholder
if my_secret_key == "PASTE_YOUR_NEW_KEY_HERE":
    st.error("STOP! You forgot to paste your API Key in agents.py line 8!")
    st.stop()

# --- 2. SETUP LLM ---
# Using the stable 'flash-latest' alias with safe rate limits
my_llm = LLM(
    model="gemini/gemini-flash-latest", 
    api_key=my_secret_key,
    temperature=0.5,
    verbose=True,
    rpm=3
)

# --- 3. AGENT DEFINITIONS ---

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



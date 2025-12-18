import os
# DISABLE TELEMETRY
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from crewai import Agent, LLM
from tools import execute_code_tool, get_columns_tool

# 1. Setup LLM
# Ensure your API key is pasted here
os.environ["GOOGLE_API_KEY"] = "AIzaSyDDIEgzGUVdQywwgg0igmW4jKc_GNUUS3Q"

# CHANGE 1: Use 'gemini-flash-latest' (More stable limits)
# CHANGE 2: Add 'rpm=5' to force the agent to work slowly and avoid errors
my_llm = LLM(
    model="gemini/gemini-flash-latest", 
    api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0.5,
    verbose=True,
    rpm=5 
)

# 2. Define Agents

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